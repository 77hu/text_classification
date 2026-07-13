"""
城池预测引擎

基于马尔可夫链转移概率 + 城池基础倍率 + 间隔因子，
计算下一轮各城池的得分，返回 Top 3 预测。
"""
from collections import defaultdict

from .models import AttackRecord

# 固定城池基础出现概率（用于预测公式的分母）
CITY_RATE = {
    "许昌": 0.2472,
    "洛阳": 0.0329,
    "成都": 0.0495,
    "建业": 0.066,
    "荆州": 0.11,
    "长安": 0.2472,
    "汉中": 0.2472,
}

# 所有候选城池
ALL_CITIES = ["洛阳", "成都", "建业", "荆州", "长安", "许昌", "汉中"]

# 需要至少多少条记录才开始返回预测
MIN_RECORDS = 100


def predict_top3():
    """主入口：计算下一轮攻击的 Top 3 预测。"""
    records = list(AttackRecord.objects.order_by("attack_time"))
    if len(records) < MIN_RECORDS:
        return None

    last_city = records[-1].tower_name
    city_names = [r.tower_name for r in records]
    return _predict_from_cities(city_names, last_city)


def predict_from_memory(city_names):
    """纯 Python 预测，不访问数据库，适用于异步上下文。"""
    if len(city_names) < MIN_RECORDS:
        return None
    last_city = city_names[-1]
    return _predict_from_cities(city_names, last_city)


def _predict_from_cities(city_names, last_city):
    """内部函数：基于城市名称列表和最后一个城市生成 Top 3。"""

    # 1) 构建马尔可夫转移矩阵
    matrix = defaultdict(lambda: defaultdict(int))
    for i in range(len(city_names) - 1):
        matrix[city_names[i]][city_names[i + 1]] += 1

    # 计算 P(city | last_city)
    if last_city in matrix:
        total = sum(matrix[last_city].values())
        trans_probs = {c: matrix[last_city].get(c, 0) / total for c in ALL_CITIES}
    else:
        trans_probs = {c: 1.0 / len(ALL_CITIES) for c in ALL_CITIES}

    # 2) 计算间隔因子
    gap_factors = _compute_gap_factors_from_names(city_names)

    # 3) 综合评分: score = P(city|last) / RATE + gap_factor * 0.2
    scores = {}
    for city in ALL_CITIES:
        score = (trans_probs[city] / CITY_RATE[city]) + (gap_factors[city] * 0.2)
        scores[city] = round(score, 4)

    # 4) 排序取 Top 3
    sorted_cities = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top3 = []
    for city, score in sorted_cities[:3]:
        top3.append({
            "name": city,
            "score": round(score, 2),
            "probability": round(trans_probs[city] * 100, 1),
            "rate": CITY_RATE[city],
            "gap_factor": round(gap_factors[city], 2),
        })

    return top3


def _compute_gap_factors_from_names(city_names):
    """计算每座城的间隔因子：gap_factor = 当前间隔轮数 / 平均间隔轮数。"""
    last_seen = {}   # city_name -> 上次出现的轮次
    gaps = {}        # city_name -> [间隔列表]

    for round_num, city in enumerate(city_names):
        if city in last_seen:
            gaps.setdefault(city, []).append(round_num - last_seen[city])
        last_seen[city] = round_num

    total_rounds = len(city_names)
    factors = {}
    for city in ALL_CITIES:
        if city not in last_seen:
            factors[city] = 2.0
            continue

        current_gap = total_rounds - 1 - last_seen[city]
        city_gaps = gaps.get(city, [])
        avg_gap = sum(city_gaps) / len(city_gaps) if city_gaps else 1

        factors[city] = current_gap / avg_gap if avg_gap > 0 else 1.0

    return factors
