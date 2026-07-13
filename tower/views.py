"""视图层：处理 HTTP 请求，返回页面或 JSON 数据。"""
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET

from .collector import TOWER_ICONS, TOWER_MAP, TOWER_RATES, collector


def _format_record(item):
    """将原始攻击记录格式化为前端需要的字段。
    从 sessionId (YYYYMMDDHHmm) 提取可读时间，如 "05-11 09:30"。
    """
    sid = item.get("sessionId", "")
    if sid and len(sid) >= 12:
        month = sid[4:6]
        day = sid[6:8]
        hour = sid[8:10]
        minute = sid[10:12]
        time_str = f"{month}-{day} {hour}:{minute}"
    else:
        time_str = "--"
    tid = item.get("hitTower", "0")
    return {
        "tower_name": item.get("towerName") or TOWER_MAP.get(tid, f"未知城池({tid})"),
        "tower_icon": TOWER_ICONS.get(tid, ""),
        "tower_rate": TOWER_RATES.get(tid, ""),
        "time": time_str,
        "predicted_cities": item.get("predicted_cities"),
        "prediction_correct": item.get("prediction_correct"),
    }


def _get_prediction():
    """返回最新预测，确保与记录中的判断结果来自同一组计算。"""
    # 动态读取，避免模块缓存导致的过期值
    from . import collector
    return collector._latest_prediction


@require_GET
def index(request):
    """渲染主页面，首次加载时展示当前倒计时和最近10条记录。"""
    records = collector.get_last_n(10)
    formatted = [_format_record(r) for r in records]
    countdown, refetch, remaining = collector.get_countdown()
    stats = collector.get_stats()
    status = collector.get_status()
    prediction = _get_prediction()
    return render(
        request,
        "tower/index.html",
        {
            "records": formatted,
            "countdown": remaining - 20 if remaining > 0 else 0,
            "stats": stats,
            "status": status,
            "prediction": prediction,
        },
    )


@require_GET
def api_data(request):
    """AJAX 接口，每 2 秒被前端调用，返回实时数据。

    Returns JSON:
        - records: 最近10条攻击记录
        - countdown: 倒计时字符串 (如 "00:42")
        - refetch: 布尔值，当倒计时 <= 5 秒时为 true，提示前端快速刷新
        - stats: 各城池占比统计
        - status: WebSocket 连接状态
        - prediction: Top 3 预测结果 (或 null)
    """
    records = collector.get_last_n(10)
    formatted = [_format_record(r) for r in records]
    countdown, refetch, _ = collector.get_countdown()
    return JsonResponse(
        {
            "records": formatted,
            "countdown": countdown,
            "refetch": refetch,
            "stats": collector.get_stats(),
            "status": collector.get_status(),
            "prediction": _get_prediction(),
        }
    )
