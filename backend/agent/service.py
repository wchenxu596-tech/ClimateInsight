"""Agent 服务编排 — 意图识别 → 工具调用 → 响应生成"""
from agent.intents import detect
from agent.tools import TOOLS, VALID_YEARS
from agent.responder import make_response
from config import DATA_YEAR

NO_TOOL_INTENTS = {"chat", "help", "unknown"}


def query(question: str, year: int = DATA_YEAR, page: str = "") -> dict:
    """处理一次Agent查询。year/page为UI上下文回退。"""
    intent_info = detect(question)

    # UI年份/页面仅作为LLM未识别时的回退
    if "year" not in intent_info or intent_info["year"] is None:
        intent_info["year"] = year
    if page and intent_info.get("intent") == "page_analysis" and "page" not in intent_info:
        intent_info["page"] = page

    intent = intent_info.get("intent", "unknown")

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
                intent_info.get("limit", 10))

        elif intent == "zones":
            result = TOOLS["get_zones"](qyear)

        elif intent == "compare":
            years = intent_info.get("years", [])
            compare_type = intent_info.get("type", "kpi")
            results = {}
            for y in years:
                if compare_type == "kpi":
                    results[y] = TOOLS["get_kpi"](y)
                else:
                    results[y] = TOOLS["get_monthly"](y)
            return make_response(intent_info, results)

        elif intent == "trend_analysis":
            years = intent_info.get("years", [2015, 2025])
            trend_data = TOOLS["get_trend_multi_year"](years)
            kpi_data = TOOLS["get_kpi_history"](years)
            result = {"trend": trend_data, "kpi": kpi_data}

        elif intent == "seasonal":
            years = [y for y in VALID_YEARS if y <= qyear][-4:] if qyear > 2017 else [y for y in VALID_YEARS if y <= qyear]
            if len(years) < 2: years = [2015, 2025]
            result = {"trend": TOOLS["get_trend_multi_year"](years), "years": years}

        elif intent == "zone_detail":
            years = [y for y in VALID_YEARS if y <= qyear]
            if len(years) < 2: years = [2015, 2025]
            result = {"zones": TOOLS["get_zones_trend"](years), "years": years}

        elif intent == "extremes":
            years = [y for y in VALID_YEARS if y <= qyear]
            if len(years) < 2: years = [2015, 2025]
            result = {"zones": TOOLS["get_zones_trend"](years), "years": years}

        elif intent == "station_query":
            st = intent_info.get("station", "")
            # 尝试模糊匹配站名
            result = {"query_station": st}
            # 直接尝试用原始输入作为ID或名称
            result["detail"] = TOOLS["get_station_detail"](st, qyear)

        elif intent == "page_analysis":
            pg = intent_info.get("page", page or "总览")
            # 拉取丰富数据：当前年 + 5年历史趋势
            recent_years = sorted([y for y in VALID_YEARS if y <= qyear])[-5:]
            if len(recent_years) < 2: recent_years = sorted(VALID_YEARS)[-5:]
            result = {"page": pg}
            # 基础数据（所有页面通用）
            result["kpi"] = TOOLS["get_kpi"](qyear)
            result["kpi_history"] = TOOLS["get_kpi_history"](recent_years)
            result["monthly"] = TOOLS["get_monthly"](qyear)
            result["zones"] = TOOLS["get_zones"](qyear)
            result["zones_trend"] = TOOLS["get_zones_trend"](recent_years)
            result["trend"] = TOOLS["get_trend_multi_year"](recent_years)
            result["years_context"] = recent_years
            # 页面专属深度数据
            if pg in ("排名", "ranking"):
                result["hottest"] = TOOLS["get_ranking"](qyear, "hottest", 5)
                result["coldest"] = TOOLS["get_ranking"](qyear, "coldest", 5)
                result["rainiest"] = TOOLS["get_ranking"](qyear, "rainiest", 5)
                result["extremes"] = TOOLS["get_ranking"](qyear, "most_extreme", 5)
            elif pg in ("预警", "alert"):
                result["extremes_ranking"] = TOOLS["get_ranking"](qyear, "most_extreme", 10)
        else:
            return make_response({"intent": "unknown", "year": qyear}, None)

        return make_response(intent_info, result)

    except Exception as e:
        return {
            "answer": f"查询出错: {str(e)[:100]}",
            "intent": intent,
            "limitations": ["数据查询异常，请稍后重试"]
        }
