"""
WebSocket 数据采集模块

连接 fluxfill.net 的 WebSocket 服务，实时接收三国游戏攻击数据。
攻击每分钟产生一次，数据格式为 sessionId (YYYYMMDDHHmm)，
通过解析 sessionId 计算倒计时。

DB 写入通过队列 + 独立同步线程完成，避免在 asyncio 上下文中
直接调用 Django ORM 导致的错误。
"""
import asyncio
import json
import queue
import threading
import time
from datetime import datetime, timezone, timedelta

import websockets

# 城池 ID 到名称的映射
TOWER_MAP = {
    "0": "初始地",
    "1": "洛阳",
    "2": "成都",
    "3": "建业",
    "4": "荆州",
    "5": "长安",
    "6": "许昌",
    "7": "汉中",
}

# 城池图标 URL（斗鱼 CDN）
TOWER_ICONS = {
    "1": "https://shark2.douyucdn.cn/front-publish/showgood-master/assets/city1-NPpGcO-d.png",
    "2": "https://shark2.douyucdn.cn/front-publish/showgood-master/assets/city2-BhEtWtnv.png",
    "3": "https://shark2.douyucdn.cn/front-publish/showgood-master/assets/city3-C6KzK1yO.png",
    "4": "https://shark2.douyucdn.cn/front-publish/showgood-master/assets/city4-DjAjOa4A.png",
    "5": "https://shark2.douyucdn.cn/front-publish/showgood-master/assets/city5-CQDjPH0G.png",
    "6": "https://shark2.douyucdn.cn/front-publish/showgood-master/assets/city6-BRwSji8X.png",
    "7": "https://shark2.douyucdn.cn/front-publish/showgood-master/assets/city5-CQDjPH0G.png",
}

# 城池倍率
TOWER_RATES = {
    "1": "30",
    "2": "20",
    "3": "15",
    "4": "9",
    "5": "4",
    "6": "4",
    "7": "4",
}

WS_URL = "wss://fluxfill.net/tower_client"
MAX_RECORDS = 200  # 内存中最多保留的条数

CST = timezone(timedelta(hours=8))  # UTC+8

# 最新预测结果（由 _attach_prediction_to_item 更新，供 views._get_prediction 读取）
_latest_prediction = None


def _parse_session_timestamp(item):
    """从 sessionId + leftTime 解析攻击发生的精确时间戳。

    sessionId (如 202605110927) 只精确到分钟，leftTime 表示攻击
    发生在该分钟的第几秒。两者结合得到精确攻击时间。
    """
    sid = item.get("sessionId", "")
    left_time = item.get("leftTime", 0)
    if sid and len(sid) >= 12:
        year = int(sid[0:4])
        month = int(sid[4:6])
        day = int(sid[6:8])
        hour = int(sid[8:10])
        minute = int(sid[10:12])
        second = int(left_time) if left_time else 0
        # second = float(left_time) if left_time else 0
        dt = datetime(year, month, day, hour, minute, second=second + 20, tzinfo=CST)
        return int(dt.timestamp())
    return int(time.time())


class DataCollector:
    """WebSocket 数据收集器，在独立线程中运行，维护攻击记录列表。

    使用队列 + 独立同步线程写入数据库，避免 asyncio 上下文
    中调用 Django ORM 导致的异常。
    """

    def __init__(self):
        self.records = []          # 原始攻击记录列表
        self.connected = False     # WebSocket 连接状态
        self._lock = threading.Lock()
        self._thread = None
        self._db_thread = None     # 数据库写入线程
        self._db_queue = queue.Queue()  # 数据库写入队列
        self._running = False

    def start(self):
        """启动采集线程和数据库写入线程（幂等）。"""
        if self._thread and self._thread.is_alive():
            return
        self._running = True
        # 启动数据库写入线程（同步上下文）
        self._db_thread = threading.Thread(target=self._db_worker, daemon=True)
        self._db_thread.start()
        # 启动 WebSocket 采集线程
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def _db_worker(self):
        """数据库写入线程：从队列中取出任务并执行（同步上下文）。"""
        from .models import AttackRecord
        from datetime import datetime as _dt

        while self._running:
            try:
                task = self._db_queue.get(timeout=1)
                if task["type"] == "single":
                    item = task["data"]
                    tid = item.get("hitTower", "0")
                    if tid == "0":
                        continue
                    ts = _parse_session_timestamp(item)
                    attack_dt = _dt.fromtimestamp(ts, tz=CST)
                    AttackRecord.objects.create(
                        tower_id=tid,
                        tower_name=TOWER_MAP.get(tid, f"未知({tid})"),
                        session_id=item.get("sessionId", ""),
                        left_time=int(item.get("leftTime", 0)) if item.get("leftTime") else 0,
                        attack_time=attack_dt,
                        predicted_cities=item.get("predicted_cities"),
                        prediction_correct=item.get("prediction_correct"),
                    )
                elif task["type"] == "batch":
                    items = task["data"]
                    existing = set(AttackRecord.objects.values_list("session_id", flat=True))
                    to_create = []
                    for item in items:
                        tid = item.get("hitTower", "0")
                        sid = item.get("sessionId", "")
                        if tid == "0" or sid in existing:
                            continue
                        existing.add(sid)
                        ts = _parse_session_timestamp(item)
                        attack_dt = _dt.fromtimestamp(ts, tz=CST)
                        to_create.append(AttackRecord(
                            tower_id=tid,
                            tower_name=TOWER_MAP.get(tid, f"未知({tid})"),
                            session_id=sid,
                            left_time=int(item.get("leftTime", 0)) if item.get("leftTime") else 0,
                            attack_time=attack_dt,
                        ))
                    if to_create:
                        AttackRecord.objects.bulk_create(to_create)
            except queue.Empty:
                continue
            except Exception as e:
                print(f"[DB Worker] Error: {e}")

    def _save_record_async(self, item):
        """将单条记录加入数据库写入队列。"""
        self._db_queue.put({"type": "single", "data": item})

    def _save_batch_async(self, items):
        """将批量记录加入数据库写入队列。"""
        self._db_queue.put({"type": "batch", "data": items})

    def _run_loop(self):
        """主循环：连接 WebSocket，断开后自动重连。"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        while self._running:
            try:
                loop.run_until_complete(self._connect())
            except Exception as e:
                print(f"[Collector] Error: {e}")
            if self._running:
                self.connected = False
                time.sleep(5)  # 断开后等待 5 秒再重连

    async def _connect(self):
        """建立 WebSocket 连接并持续接收消息。"""
        async for ws in websockets.connect(WS_URL):
            self.connected = True
            try:
                async for message in ws:
                    self._handle_message(message)
            except websockets.ConnectionClosed:
                self.connected = False
                break

    def _handle_message(self, raw):
        """处理一条 WebSocket 消息。
        - history: 首次连接时收到的历史数据（约 4300 条）
        - update:  每分钟新产生的攻击数据
        """
        try:
            data = json.loads(raw)
            if data.get("type") == "history":
                with self._lock:
                    self.records = data.get("data", [])[:MAX_RECORDS]
                # 批量保存历史记录到数据库（通过队列异步写入）
                self._save_batch_async(data.get("data", []))
                # 预计算预测，避免重启后首次预测框为空
                self._precompute_prediction()
            elif data.get("type") == "update":
                item = data.get("data", {})
                # 用已有历史（不含本轮）预测本轮，立即比对正确性
                self._attach_prediction_to_item(item)
                with self._lock:
                    # 新记录插入头部，保持时间倒序
                    self.records.insert(0, item)
                    self.records = self.records[:MAX_RECORDS]
                # 持久化单条新攻击（通过队列异步写入）
                self._save_record_async(item)
        except (json.JSONDecodeError, KeyError):
            pass

    def _attach_prediction_to_item(self, item):
        """为单条新攻击记录生成预测，附加到 item dict 上。

        基于已有历史（不含本轮新攻击）计算对**本轮**的预测，
        然后用本轮实际结果立即判断正确/错误。
        """
        global _latest_prediction
        from .predictor import predict_from_memory

        with self._lock:
            city_names = [r.get("towerName") or TOWER_MAP.get(r.get("hitTower", "0"), "")
                          for r in reversed(self.records)
                          if r.get("hitTower") != "0"]

        top3 = predict_from_memory(city_names)
        tid = item.get("hitTower", "0")
        if top3:
            predicted_names = [p["name"] for p in top3]
            item["predicted_cities"] = ",".join(predicted_names)
            actual_name = TOWER_MAP.get(tid, "")
            item["prediction_correct"] = actual_name in predicted_names
            _latest_prediction = top3
        else:
            item["predicted_cities"] = None
            item["prediction_correct"] = None

    def _precompute_prediction(self):
        """基于已有历史记录为每条记录计算预测，避免重启后预测框为空。

        按时间正序遍历，对第 i 条记录用前 i-1 条历史做预测，
        然后用第 i 条的实际结果判断正确/错误，与 update 路径逻辑一致。
        """
        global _latest_prediction
        from .predictor import predict_from_memory

        with self._lock:
            valid = [r for r in reversed(self.records) if r.get("hitTower") != "0"]

        for i, record in enumerate(valid):
            if i < 100:
                record["predicted_cities"] = None
                record["prediction_correct"] = None
                continue

            city_names = [r.get("towerName") or TOWER_MAP.get(r.get("hitTower", "0"), "")
                          for r in valid[:i]]

            top3 = predict_from_memory(city_names)
            tid = record.get("hitTower", "0")
            if top3:
                predicted_names = [p["name"] for p in top3]
                record["predicted_cities"] = ",".join(predicted_names)
                actual_name = TOWER_MAP.get(tid, "")
                record["prediction_correct"] = actual_name in predicted_names
                _latest_prediction = top3
            else:
                record["predicted_cities"] = None
                record["prediction_correct"] = None

    def get_last_n(self, n=10):
        """返回最近 n 条有效攻击记录（排除"初始地"）。"""
        with self._lock:
            valid = [r for r in self.records if r.get("hitTower") != "0"]
            return valid[:n]

    def get_countdown(self):
        """计算距离下一次攻击的剩余秒数。

        算法: 从最新攻击的 sessionId 解析出攻击发生时间 ts，
        用 60 - (当前时间 - ts) 得到剩余秒数。
        当剩余 <= 5 秒时返回 refetch=True，通知前端主动刷新。

        Returns:
            (countdown_str, refetch, remaining_int): 如 ("00:42", False, 42) 或 ("即将开始", True, 5)
        """
        with self._lock:
            if not self.records:
                return "--:--", False, 0
            latest = None
            for r in self.records:
                if r.get("hitTower") != "0":
                    latest = r
                    break
            if not latest:
                return "--:--", False, 0
            ts = _parse_session_timestamp(latest)
            now = int(time.time())
            elapsed = now - ts
            # 攻击间隔为 60 秒（sessionId 对齐分钟边界）
            remaining = 60 - elapsed
            if remaining <= 5:
                return "即将开始", True, remaining   # <= 5 秒，提示前端快速刷新
            if remaining <= 0:
                return "即将开始", False, remaining
            return f"{remaining // 60:02d}:{remaining % 60:02d}", False, remaining

    def get_stats(self):
        """统计最近 100 次有效攻击中各城池的占比。"""
        with self._lock:
            stats = {}
            for tid in TOWER_MAP:
                if tid != "0":
                    stats[tid] = {"name": TOWER_MAP[tid], "rate": TOWER_RATES[tid], "count": 0}
            valid_count = 0
            for r in self.records:
                if valid_count >= 100:
                    break
                tid = r.get("hitTower")
                if tid != "0" and tid in stats:
                    stats[tid]["count"] += 1
                    valid_count += 1
            if valid_count == 0:
                return []
            result = []
            for tid in sorted(stats.keys(), key=lambda x: int(x)):
                if tid == "0":
                    continue
                s = stats[tid]
                s["percent"] = round(s["count"] / valid_count * 100, 1)
                result.append(s)
            return result

    def get_status(self):
        """返回连接状态: 'connected' 或 'disconnected'。"""
        return "connected" if self.connected else "disconnected"

    def get_last_attack(self):
        """返回最新一条有效攻击记录。"""
        with self._lock:
            for r in self.records:
                if r.get("hitTower") != "0":
                    return r
            return None


collector = DataCollector()
