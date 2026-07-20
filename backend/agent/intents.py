"""意图识别 — 规则优先（关键词+正则），可选LLM增强"""
import re
from config import DATA_YEAR

YEAR_PAT = re.compile(r"(20\d{2})\s*年")

def detect(question: str) -> dict:
    """返回 {'intent':..., 'category':..., 'limit':..., 'year':...} 或 {'intent':'unknown'}"""
    q = question.strip().lower()
    year = DATA_YEAR
    m = YEAR_PAT.search(question)
    if m: year = int(m.group(1))

    # KPI / 全球均温
    if any(w in q for w in ["全球平均", "年均温", "平均气温", "kpi", "指标"]):
        return {"intent": "kpi", "year": year}

    # 月度
    if any(w in q for w in ["月度", "每月", "各月", "12个月", "月均"]):
        return {"intent": "monthly", "year": year}

    # 排名 — 最热
    if any(w in q for w in ["最热", "最高温", "高温", "最烫"]):
        limit = _extract_limit(q)
        return {"intent": "ranking", "category": "hottest", "limit": limit, "year": year}

    # 排名 — 最冷
    if any(w in q for w in ["最冷", "最低温", "低温", "最冻", "最寒"]):
        limit = _extract_limit(q)
        return {"intent": "ranking", "category": "coldest", "limit": limit, "year": year}

    # 排名 — 降水
    if any(w in q for w in ["降水", "下雨", "最多雨", "降雨", "雨水"]):
        limit = _extract_limit(q)
        return {"intent": "ranking", "category": "rainiest", "limit": limit, "year": year}

    # 排名 — 极端
    if any(w in q for w in ["极端", "恶劣天气", "极端天气"]):
        limit = _extract_limit(q)
        return {"intent": "ranking", "category": "most_extreme", "limit": limit, "year": year}

    # 气候带
    if any(w in q for w in ["气候带", "热带", "温带", "寒带", "分布"]):
        return {"intent": "zones", "year": year}

    # 帮助
    if any(w in q for w in ["帮助", "能做什么", "怎么用", "功能"]):
        return {"intent": "help", "year": year}

    return {"intent": "unknown", "year": year}

def _extract_limit(q: str) -> int:
    m = re.search(r"前?\s*(\d+)\s*(个|名|位|条|站)", q)
    if m: return min(int(m.group(1)), 15)
    m = re.search(r"top\s*(\d+)", q)
    if m: return min(int(m.group(1)), 15)
    return 10
