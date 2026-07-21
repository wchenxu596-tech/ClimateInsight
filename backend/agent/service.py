"""Agent 服务编排 — 意图识别 → 工具调用 → 响应生成"""
from agent.intents import detect
from agent.tools import TOOLS
from agent.responder import make_response

# 无需调用工具的意图（chat/help/unknown 直接返回模板）
NO_TOOL_INTENTS = {"chat", "help", "unknown"}


def query(question: str, year: int = 2024) -> dict:
    """处理一次Agent查询，返回完整响应字典。
    year 参数覆盖意图识别出的年份，确保数据一致性。"""
    intent_info = detect(question)
    intent_info["year"] = year  # 优先使用请求参数
    intent = intent_info.get("intent", "unknown")

    # 闲聊、帮助、未知 → 直接生成回复，不查数据库
    if intent in NO_TOOL_INTENTS:
        return make_response(intent_info, None)

    # 调用工具
    try:
        if intent == "kpi":
            result = TOOLS["get_kpi"](year)
        elif intent == "monthly":
            result = TOOLS["get_monthly"](year)
        elif intent == "ranking":
            result = TOOLS["get_ranking"](
                year,
                intent_info.get("category", "hottest"),
                intent_info.get("limit", 10)
            )
        elif intent == "zones":
            result = TOOLS["get_zones"](year)
        else:
            return make_response({"intent": "unknown", "year": year}, None)

        return make_response(intent_info, result)
    except Exception as e:
        return {
            "answer": f"查询出错: {str(e)[:100]}",
            "intent": intent,
            "limitations": ["数据查询异常，请稍后重试"]
        }
