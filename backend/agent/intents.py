"""意图识别 — LLM优先 + 规则回退"""
import re, json
from urllib.request import Request, urlopen
from urllib.error import URLError
from config import AGENT_ENABLED, LLM_BASE_URL, LLM_API_KEY, LLM_MODEL, DATA_YEAR
from agent.prompts import SYSTEM_PROMPT, VALID_INTENTS, VALID_CATEGORIES, VALID_YEARS_LIST, EXPECTED_KEYS

YEAR_PAT = re.compile(r"(20\d{2})\s*年")
MONTH_RANGE_PAT = re.compile(r"(\d{1,2})\s*(?:月|到|至|\-|~)\s*(\d{1,2})\s*月?")


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
            "max_tokens": 250
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
        if not isinstance(result, dict): return None
        if "intent" not in result or result["intent"] not in VALID_INTENTS:
            return None

        intent = result["intent"]
        allowed_keys = EXPECTED_KEYS[intent]
        extra = set(result.keys()) - allowed_keys
        if extra: return None

        # ranking 校验
        if intent == "ranking":
            cat = result.get("category", "hottest")
            if cat not in VALID_CATEGORIES: return None
            limit = result.get("limit", 10)
            if not isinstance(limit, int) or limit < 1: limit = 10
            result["limit"] = min(limit, 15)
            result["category"] = cat

        # monthly 校验
        if intent == "monthly":
            months = result.get("months")
            if months is not None:
                if not isinstance(months, list) or not all(isinstance(m, int) and 1 <= m <= 12 for m in months):
                    result.pop("months", None)

        # compare / trend_analysis 校验
        if intent in ("compare", "trend_analysis"):
            years = result.get("years")
            if not isinstance(years, list) or not all(y in VALID_YEARS_LIST for y in years):
                return None
            result["years"] = sorted(years)

        # station_query 校验
        if intent == "station_query":
            st = result.get("station", "")
            if not isinstance(st, str) or len(st) < 1:
                return None

        # page_analysis 校验
        if intent == "page_analysis":
            page = result.get("page", "")
            if not isinstance(page, str):
                return None

        # 年份处理：LLM提供年份才使用，不强制设置默认值
        llm_year = result.get("year")
        if llm_year is not None and llm_year in VALID_YEARS_LIST:
            result["year"] = llm_year
        elif "year" in allowed_keys:
            result.pop("year", None)  # 让UI年份优先
        else:
            result.pop("year", None)

        return result

    except Exception:
        return None


# ═══════════════════════════════════════════
#  规则引擎（兜底）
# ═══════════════════════════════════════════
def detect_rules(question: str) -> dict:
    """返回 {'intent':..., ...} 或 {'intent':'unknown'}"""
    q = question.strip().lower()
    year = None  # 不设置默认年份，让UI年份优先
    m = YEAR_PAT.search(question)
    if m:
        y = int(m.group(1))
        if y in VALID_YEARS_LIST:
            year = y

    # ── 闲聊 ──
    if any(w in q for w in ["你是谁", "你叫什么", "你的名字", "介绍一下自己", "你是干什么的"]):
        return {"intent": "chat"}
    if any(w in q for w in ["你好", "嗨", "hello", "hi"]) and len(q) <= 5:
        return {"intent": "chat"}

    # ── 帮助 ──
    if any(w in q for w in ["帮助", "能做什么", "怎么用", "功能", "怎么看", "在哪里看", "怎么查", "教我怎么", "指导", "在哪"]):
        return {"intent": "help"}

    # 构建带年份的返回（仅当用户明确提到年份时）
    def _r(intent, **extra):
        result = {"intent": intent, **extra}
        if year is not None:
            result["year"] = year
        return result

    # ── 页面分析 ──
    if any(w in q for w in ["分析当前页面", "当前页", "这个页面", "这个图表", "解读一下", "帮我分析当前", "评估"]):
        return _r("page_analysis")

    # ── 季节分析 ──
    if any(w in q for w in ["季节", "春夏秋冬", "四季", "哪个季节"]):
        return _r("seasonal")

    # ── 气候带趋势（具体）──
    if any(w in q for w in ["气候带温度", "气候带变化", "热带温度", "温带温度", "哪个气候带升温"]):
        return _r("zone_detail")

    # ── 极端事件趋势 / 异常检测 ──
    if any(w in q for w in ["极端事件变化", "热浪增加", "极端天气趋势", "寒潮变化",
                             "极端事件增多", "极端事件增加", "极端事件趋势",
                             "极端事件最多", "异常检测", "温度异常", "极端事件"]):
        return _r("extremes")

    # ── 站点查询 ──
    st_match = re.search(r"(\S+?)(?:站|机场|基地)\S*的?(?:数据|温度|降水|天气|气候)", question)
    if st_match:
        return _r("station_query", station=st_match.group(1))

    # ── KPI / 全球均温 ──
    if any(w in q for w in ["全球平均", "年均温", "平均气温", "平均温度", "kpi", "指标", "全球气候", "全球均温", "全球温度", "气温多少", "温度多少", "多热", "气候怎么样", "气候如何"]):
        return _r("kpi")

    # ── 月度 ──
    if any(w in q for w in ["月度", "每月", "各月", "12个月", "月均", "月气温", "月温度"]):
        result = _r("monthly")
        mo_match = _extract_months(question)
        if mo_match: result["months"] = mo_match
        return result

    # ── 排名 — 最热 ──
    if any(w in q for w in ["最热", "最高温", "高温", "最烫", "温度最高", "哪个最热", "哪里最热", "最热的地方"]):
        return _r("ranking", category="hottest", limit=_extract_limit(q))

    # ── 排名 — 最冷 ──
    if any(w in q for w in ["最冷", "最低温", "低温", "最冻", "最寒", "哪个最冷", "哪里最冷", "最冷的地方"]):
        return _r("ranking", category="coldest", limit=_extract_limit(q))

    # ── 排名 — 降水 ──
    if any(w in q for w in ["降水", "下雨", "最多雨", "降雨", "雨水", "雨量", "潮湿", "哪里雨多", "哪里降水"]):
        return _r("ranking", category="rainiest", limit=_extract_limit(q))

    # ── 排名 — 极端 ──
    if any(w in q for w in ["极端站点", "极端天气站点", "恶劣天气", "极端天气最多", "糟糕天气"]):
        return _r("ranking", category="most_extreme", limit=_extract_limit(q))

    # ── 多年趋势（放在具体意图之后，作为温度变化的兜底）──
    if any(w in q for w in ["变暖趋势", "多年变", "这些年", "长期趋势", "温度走势", "升温趋势", "温度上升了", "变暖了多少", "温度趋势", "温度变化"]):
        return _r("trend_analysis", years=[2015, 2025])

    # ── 气候带 ──
    if any(w in q for w in ["气候带", "热带", "温带", "寒带", "分布", "气候类型"]):
        return _r("zones")

    # ── 对比（简单匹配） ──
    years_found = sorted(set(int(m) for m in re.findall(r"(20\d{2})", question) if int(m) in VALID_YEARS_LIST))
    if len(years_found) >= 2:
        return {"intent": "compare", "type": "kpi", "years": years_found[:4]}

    return _r("unknown")


def _extract_limit(q: str) -> int:
    m = re.search(r"前?\s*(\d+)\s*(个|名|位|条|站)", q)
    if m: return min(int(m.group(1)), 15)
    m = re.search(r"top\s*(\d+)", q)
    if m: return min(int(m.group(1)), 15)
    return 10

def _extract_months(question: str) -> list | None:
    m = MONTH_RANGE_PAT.search(question)
    if not m: return None
    start, end = int(m.group(1)), int(m.group(2))
    if start < 1 or end > 12 or start > end: return None
    return list(range(start, end + 1))


# ═══════════════════════════════════════════
#  统一入口 — LLM优先，失败回退规则
# ═══════════════════════════════════════════
def detect(question: str) -> dict:
    llm_result = detect_llm(question)
    if llm_result: return llm_result
    return detect_rules(question)
