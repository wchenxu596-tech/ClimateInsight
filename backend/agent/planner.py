"""Planner — NLU 结果归一化 + LLM Function Calling + 规则回退

手册 Section 4.2 要求：
- 规则预解析快速覆盖确定性请求
- LLM Function Calling 只返回 AnalysisPlan
- 对 LLM 输出严格 Schema 验证
- 失败时回退规则引擎或请求用户澄清
"""
import json, re
from urllib.request import Request, urlopen
from config import AGENT_ENABLED, LLM_BASE_URL, LLM_API_KEY, LLM_MODEL
from agent.schemas import AnalysisPlan, validate_plan, VALID_INTENTS, VALID_METRICS
from agent.catalog import ALLOWED_AGG_FUNCTIONS, CLIMATE_ZONES

YEAR_PAT = re.compile(r"(20\d{2})\s*年")
SEASON_PAT = re.compile(r"(春|夏|秋|冬)季")
MONTH_PAT = re.compile(r"(\d{1,2})\s*月")

# ── LLM Function Calling Schema ──
ANALYSIS_PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "intents": {
            "type": "array", "items": {"type": "string", "enum": VALID_INTENTS},
            "description": "分析意图列表"
        },
        "time_groups": {
            "type": "array", "items": {
                "type": "object",
                "properties": {
                    "start": {"type": "integer", "minimum": 1900, "maximum": 2100},
                    "end":   {"type": "integer", "minimum": 1900, "maximum": 2100},
                    "label": {"type": "string"}
                },
                "required": ["start", "end"]
            }
        },
        "granularity": {"type": "string", "enum": ["day","month","year"]},
        "season": {"type": "array", "items": {"type": "integer", "minimum": 1, "maximum": 12}},
        "spatial_filter": {
            "type": "object",
            "properties": {
                "type":  {"type": "string", "enum": ["region","station","climate_zone","bbox","country","all"]},
                "value": {}
            }
        },
        "metrics": {"type": "array", "items": {"type": "string", "enum": VALID_METRICS}},
        "aggregation": {"type": "string", "enum": list(ALLOWED_AGG_FUNCTIONS.keys())},
        "group_by": {"type": "array", "items": {"type": "string"}},
        "chart_goal": {"type": "string", "enum": ["trend","compare","distribution","proportion","correlation","map","table"]},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1}
    },
    "required": ["intents"]
}

FUNCTION_DEF = {
    "name": "create_analysis_plan",
    "description": "Create a structured climate analysis plan from the user's natural language query",
    "parameters": ANALYSIS_PLAN_SCHEMA
}

SYSTEM_PROMPT_V2 = """你是一个气候数据分析计划生成器。将用户的中文自然语言请求转换为结构化的分析计划JSON。

## 可用要素
{temperature, precipitation, extreme_events, wind, frost, snow, thunder}

## 可用聚合
{mean, sum, min, max, count, std}

## 可用空间过滤
{climate_zone: [tropical, temperate, arid, continental, polar]}
{bbox: [lat_min, lat_max, lon_min, lon_max]}

## 规则
- 年份从问题中提取（如"2020年"→2020）；若未提年份，不填 time_groups
- 季节：春=3-5月, 夏=6-8月, 秋=9-11月, 冬=12,1-2月
- 不要编造超出数据范围的过滤条件
- confidence 表示你对解析结果的置信度(0-1)
"""


def plan_via_llm(question: str) -> tuple[dict | None, float]:
    """LLM Function Calling → AnalysisPlan JSON"""
    if not AGENT_ENABLED or not LLM_API_KEY:
        return None, 0.0

    try:
        body = json.dumps({
            "model": LLM_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT_V2},
                {"role": "user", "content": question}
            ],
            "functions": [FUNCTION_DEF],
            "function_call": {"name": "create_analysis_plan"},
            "temperature": 0,
            "max_tokens": 500
        }).encode("utf-8")

        req = Request(
            f"{LLM_BASE_URL}/chat/completions",
            data=body,
            headers={"Authorization": f"Bearer {LLM_API_KEY}", "Content-Type":"application/json"}
        )
        resp = urlopen(req, timeout=8)
        raw = json.loads(resp.read().decode("utf-8"))
        msg = raw["choices"][0]["message"]

        if "function_call" in msg:
            plan_dict = json.loads(msg["function_call"]["arguments"])
        elif "content" in msg:
            content = msg["content"].strip()
            if content.startswith("```"): content = content.split("\n",1)[1].rsplit("\n```",1)[0]
            plan_dict = json.loads(content)
        else:
            return None, 0.0

        plan, errors = validate_plan(plan_dict)
        if plan:
            plan.source = "llm"
            plan.raw_question = question
            return plan.to_dict(), plan.confidence
        return None, 0.0

    except Exception:
        return None, 0.0


def plan_via_rules(question: str) -> dict:
    """规则引擎预解析 → AnalysisPlan（兜底）"""
    q = question.strip()
    plan = {"intents": [], "source": "rule", "raw_question": question}

    # 年份
    years = [int(m) for m in re.findall(r"(20\d{2})", q) if 2015 <= int(m) <= 2025]
    if years:
        plan["time_groups"] = [{"start": min(years), "end": max(years), "label": f"{min(years)}-{max(years)}"}]

    # 季节
    season_map = {"春":[3,4,5],"夏":[6,7,8],"秋":[9,10,11],"冬":[12,1,2]}
    for s, ms in season_map.items():
        if s in q: plan["season"] = ms; break

    # 空间
    for zone in CLIMATE_ZONES:
        if zone in q.lower():
            plan["spatial_filter"] = {"type":"climate_zone","value":zone}
            break

    # 意图
    if any(w in q for w in ["趋势","变化","变暖","长期","多年"]):
        plan["intents"] = ["trend_analysis"]; plan["chart_goal"] = "trend"
    elif any(w in q for w in ["对比","比较","哪个更","和"]):
        plan["intents"] = ["compare"]; plan["chart_goal"] = "compare"
    elif any(w in q for w in ["异常","极端事件增加","极端天气趋势"]):
        plan["intents"] = ["extremes"]; plan["chart_goal"] = "trend"
    elif any(w in q for w in ["排名","最热","最冷","TOP","前"]):
        plan["intents"] = ["ranking"]; plan["chart_goal"] = "compare"
    elif any(w in q for w in ["分布","气候带","占比"]):
        plan["intents"] = ["zones"]; plan["chart_goal"] = "proportion"
    elif any(w in q for w in ["季节","春夏秋冬","哪个季节"]):
        plan["intents"] = ["seasonal"]; plan["chart_goal"] = "compare"
    elif any(w in q for w in ["全球","总览","概况","KPI"]):
        plan["intents"] = ["kpi"]; plan["chart_goal"] = "table"
    else:
        plan["intents"] = ["summary"]

    plan["granularity"] = "year"
    plan["metrics"] = ["avg_temperature"]

    return plan


def create_plan(question: str) -> AnalysisPlan:
    """统一入口：LLM 优先 → 规则回退"""
    llm_plan, confidence = plan_via_llm(question)
    if llm_plan and confidence >= 0.5:
        plan, _ = validate_plan(llm_plan)
        if plan: return plan

    rule_plan = plan_via_rules(question)
    plan, _ = validate_plan(rule_plan)
    return plan if plan else AnalysisPlan(source="rule")
