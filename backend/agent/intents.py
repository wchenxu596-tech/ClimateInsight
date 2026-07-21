"""意图识别 — LLM优先 + 规则回退"""
import re, json
from urllib.request import Request, urlopen
from urllib.error import URLError
from config import AGENT_ENABLED, LLM_BASE_URL, LLM_API_KEY, LLM_MODEL, DATA_YEAR
from agent.prompts import SYSTEM_PROMPT, VALID_INTENTS, VALID_CATEGORIES, EXPECTED_KEYS

YEAR_PAT = re.compile(r"(20\d{2})\s*年")


# ═══════════════════════════════════════════
#  LLM 意图识别
# ═══════════════════════════════════════════
def detect_llm(question: str) -> dict | None:
    """调用大模型进行意图识别，失败/超时/格式不对 → 返回 None"""
    if not AGENT_ENABLED or not LLM_API_KEY:
        return None

    try:
        body = json.dumps({
            "model": LLM_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": question}
            ],
            "temperature": 0,
            "max_tokens": 200
        }).encode("utf-8")

        req = Request(
            f"{LLM_BASE_URL}/chat/completions",
            data=body,
            headers={
                "Authorization": f"Bearer {LLM_API_KEY}",
                "Content-Type": "application/json"
            }
        )
        resp = urlopen(req, timeout=5)
        raw = json.loads(resp.read().decode("utf-8"))
        content = raw["choices"][0]["message"]["content"].strip()

        # 清理可能的 markdown 代码块
        if content.startswith("```"):
            lines = content.split("\n")
            lines = lines[1:] if lines[0].startswith("```") else lines
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            content = "\n".join(lines).strip()
            if content.startswith("json"):
                content = content[4:].strip()

        result = json.loads(content)

        # ── JSON Schema 校验 ──
        if not isinstance(result, dict):
            return None
        if "intent" not in result or result["intent"] not in VALID_INTENTS:
            return None

        intent = result["intent"]
        allowed_keys = EXPECTED_KEYS[intent]

        # 拒绝多余字段
        extra = set(result.keys()) - allowed_keys
        if extra:
            return None

        if intent == "ranking":
            cat = result.get("category", "hottest")
            if cat not in VALID_CATEGORIES:
                return None
            limit = result.get("limit", 10)
            if not isinstance(limit, int) or limit < 1:
                limit = 10
            result["limit"] = min(limit, 15)
            result["category"] = cat
        else:
            result.pop("category", None)
            result.pop("limit", None)

        result["year"] = DATA_YEAR
        return result

    except Exception:
        return None


# ═══════════════════════════════════════════
#  规则引擎（兜底）
# ═══════════════════════════════════════════
def detect_rules(question: str) -> dict:
    """返回 {'intent':..., 'category':..., 'limit':..., 'year':...} 或 {'intent':'unknown'}"""
    q = question.strip().lower()
    year = DATA_YEAR
    m = YEAR_PAT.search(question)
    if m:
        year = int(m.group(1))

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
    if m:
        return min(int(m.group(1)), 15)
    m = re.search(r"top\s*(\d+)", q)
    if m:
        return min(int(m.group(1)), 15)
    return 10


# ═══════════════════════════════════════════
#  统一入口 — LLM优先，失败回退规则
# ═══════════════════════════════════════════
def detect(question: str) -> dict:
    """意图识别：LLM优先 → 规则兜底"""
    llm_result = detect_llm(question)
    if llm_result:
        return llm_result
    return detect_rules(question)
