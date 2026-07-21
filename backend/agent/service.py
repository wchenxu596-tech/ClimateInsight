"""Agent 服务编排 — 意图识别 → 工具调用 → 响应生成"""
from agent.intents import detect
from agent.tools import TOOLS
from agent.responder import make_response
from config import DATA_YEAR

NO_TOOL_INTENTS = {"chat", "help", "unknown"}


def query(question: str, year: int = DATA_YEAR) -> dict:
    """处理一次Agent查询。year参数仅在LLM未识别出年份时作为回退。"""
    intent_info = detect(question)
    intent = intent_info.get("intent", "unknown")

    # UI年份仅作为LLM未识别时的回退
    if "year" not in intent_info or intent_info["year"] is None:
        intent_info["year"] = year

    if intent in NO_TOOL_INTENTS:
        return make_response(intent_info, None)

    try:
        qyear = intent_info.get("year", year)

        if intent == "kpi":
            result = TOOLS["get_kpi"](qyear)
        elif intent == "monthly":
            result = TOOLS["get_monthly"](qyear)
        elif intent == "ranking":
            result = TOOLS["get_ranking"](
                qyear,
                intent_info.get("category", "hottest"),
                intent_info.get("limit", 10)
            )
        elif intent == "zones":
            result = TOOLS["get_zones"](qyear)
        elif intent == "compare":
            years = intent_info.get("years", [])
            results = {}
            for y in years:
                if intent_info.get("type") == "kpi":
                    results[y] = TOOLS["get_kpi"](y)
                else:
                    results[y] = TOOLS["get_monthly"](y)
            return make_response(intent_info, results)
        else:
            return make_response({"intent": "unknown", "year": qyear}, None)

        return make_response(intent_info, result)
    except Exception as e:
        return {
            "answer": f"查询出错: {str(e)[:100]}",
            "intent": intent,
            "limitations": ["数据查询异常，请稍后重试"]
        }
