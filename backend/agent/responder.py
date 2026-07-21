"""响应生成器 — 模板模式（LLM可选增强）"""
from config import AGENT_ENABLED, DATA_YEAR

ZONE_CN = {"tropical": "热带", "temperate": "温带", "continental": "大陆性", "polar": "寒带", "arid": "干旱"}

# 站名中文简表
STATION_CN = {
    "AMUNDSEN SCOTT, AY": "阿蒙森-斯科特站", "ARAFAT, SA": "阿拉法特",
    "VOSTOK, AY": "东方站", "SITEKI, WZ": "锡泰基", "CONCORDIA, AQ": "康科迪亚站",
    "DOME C II, AQ": "冰穹C二号", "MARBLE POINT, AY": "大理石角",
    "MAHABALESHWAR, IN": "默哈伯莱什沃尔", "HONAVAR, IN": "霍纳瓦尔",
    "JOKKMOKK FPL, SW": "约克莫克", "HALLEY, AY": "哈雷站",
    "KHLONG YAI, TH": "空艾", "KAYES DAG DAG, ML": "卡伊",
    "MINA, SA": "米纳", "KOSRAE INTERNATIONAL AIRPORT, FM FM": "科斯雷机场",
    "MATAM OURO SOGUI, SG": "马塔姆", "PREAH VIHEAR, CB": "柏威夏",
    "PODOR, SG": "波多尔", "NARA KEIBANE, ML": "纳拉",
    "YELIMANE, ML": "耶利马内", "LINGUERE, SG": "林盖尔",
    "TAMBACOUNDA, SG": "坦巴昆达", "TILLABERY, NG": "蒂拉贝里",
    "NIORO DU SAHEL, ML": "纽罗", "BERNARD HARBOUR, CA": "伯纳德港",
    "COLVILLE LAKE NWT, CA": "科尔维尔湖", "DAWEI, BM": "土瓦",
    "YE, BM": "耶", "MAO, CD": "马奥", "ZAKATALA, AJ": "扎卡塔拉",
    "GAVAR, AM": "加瓦尔", "FAHUD AUT, MU": "法胡德",
    "BALDRICK AWS, AY": "鲍德里克站", "CAPE PHILLIPS, AY": "菲利普斯角",
    "DOME PLATEAU DOME A, AY": "冰穹A", "DOME PLATEAU EAGLE, AY": "冰穹鹰",
    "HALVFARRYGGEN EP11, AY": "半脊EP11", "LAW DOME SUMMIT, AY": "劳穹顶",
    "MID POINT, AY": "中点站", "PRIESTLEY GLACIER, AY": "普里斯特利冰川",
    "S.A.N.A.E. AWS, AY": "南非科考站", "UNIVERSITY WI ID 8917 SKI BLU, AY": "威大8917站",
    "UNIVERSITY WI ID 8925 LIMBERT AWS, AY": "威大8925站",
    "HALIM PERDANAKUSUMA INTERNATIONAL, ID": "哈利姆机场",
    "KOKONAO TIMUKA, ID": "科科纳奥", "SAM RATULANGI, ID": "萨姆拉图兰吉",
    "SANTO PEKOA INTERNATIONAL, NH": "桑托佩可亚", "OSMANY INTERNATIONAL, BG": "奥斯曼尼机场",
    "MILFORD SOUNDN AWS, NZ": "米尔福德峡湾", "SECRETARY ISLAND AWS, NZ": "秘书岛",
}

MONTH_NAMES = ["1月", "2月", "3月", "4月", "5月", "6月", "7月", "8月", "9月", "10月", "11月", "12月"]


def make_response(intent_info: dict, tool_result) -> dict:
    """根据意图和工具结果生成前端可用的回答"""
    intent = intent_info.get("intent", "unknown")
    year = intent_info.get("year", DATA_YEAR)
    data = {"answer": "", "intent": intent}

    if intent == "kpi":
        data["answer"] = f"{year} 年全球气候核心指标如下："
        data["table"] = {"columns": ["指标", "数值", "单位"], "rows": [
            [r["kpi_desc"], str(r["kpi_value"]), r["kpi_unit"]] for r in tool_result
        ]}

    elif intent == "monthly":
        # 月份过滤
        rows = tool_result
        months_filter = intent_info.get("months")
        if months_filter and isinstance(months_filter, list) and len(months_filter) > 0:
            valid_set = set(months_filter)
            rows = [r for r in rows if r["obs_month"] in valid_set]
            mo_range = f"{months_filter[0]}~{months_filter[-1]}月"
            data["answer"] = f"{year} 年 {mo_range} 平均温度（全球气象站均值）："
        else:
            data["answer"] = f"{year} 年各月平均温度（全球气象站均值）："

        data["chart"] = {
            "type": "line",
            "x": [f"{r['obs_month']}月" for r in rows],
            "y": [float(r["avg_temp"]) for r in rows],
            "name": "均温(°C)"
        }

    elif intent == "ranking":
        cat = intent_info.get("category", "hottest")
        cat_names = {"hottest": "最高温", "coldest": "最低温", "rainiest": "降水量", "most_extreme": "极端天数"}
        unit = "°C" if cat in ("hottest", "coldest") else ("mm" if cat == "rainiest" else "天")
        data["answer"] = f"{year} 年{cat_names.get(cat, cat)}排名："
        data["table"] = {"columns": ["排名", "站点", f"{cat_names.get(cat, cat)}({unit})"], "rows": [
            [str(r["rank_num"]), STATION_CN.get(r["station_name"], r["station_name"]), str(r["value"])] for r in tool_result
        ]}
        data["chart"] = {
            "type": "bar",
            "x": [STATION_CN.get(r["station_name"], r["station_name"])[:10] for r in tool_result],
            "y": [float(r["value"]) for r in tool_result],
            "name": f"{cat_names.get(cat, cat)}({unit})"
        }

    elif intent == "zones":
        data["answer"] = f"{year} 年气候带分布："
        data["table"] = {"columns": ["气候带", "站点数"], "rows": [
            [ZONE_CN.get(r["climate_zone"], r["climate_zone"]), str(r["cnt"])] for r in tool_result
        ]}
        data["chart"] = {
            "type": "pie",
            "x": [ZONE_CN.get(r["climate_zone"], r["climate_zone"]) for r in tool_result],
            "y": [int(r["cnt"]) for r in tool_result],
            "name": "站点数"
        }

    elif intent == "compare":
        years = intent_info.get("years", [])
        if not years or not tool_result:
            data["answer"] = "暂无对比数据。"
            return data

        compare_type = intent_info.get("type", "kpi")
        if compare_type == "kpi":
            # 对比KPI：年均温
            temps = {}
            for y, rows in tool_result.items():
                for r in rows:
                    if r.get("kpi_name") == "global_avg_temp":
                        temps[y] = r.get("kpi_value")
            lines = [f"{y} 年全球年均温：{temps.get(y, '--')}°C" for y in years]
            data["answer"] = "多年对比结果：\n" + "\n".join(lines)
            data["chart"] = {
                "type": "bar",
                "x": [f"{y}年" for y in years],
                "y": [float(temps.get(y, 0) or 0) for y in years],
                "name": "年均温(°C)"
            }

    elif intent == "chat":
        data["answer"] = (
            "👋 你好！我是 ClimateInsight 气候智能分析助手。\n\n"
            "我可以帮你查询 NOAA GSOD 2024 年全球气候数据：\n"
            "• 全球平均气温等核心指标\n"
            "• 各月温度变化趋势\n"
            "• 最热/最冷/降水最多/极端天气最多的站点排名\n"
            "• 气候带分布情况\n\n"
            "直接输入问题即可，如「全球平均气温？」「最热的5个站点？」「5到10月温度变化？」"
        )
        data.pop("limitations", None)

    elif intent == "help":
        data["answer"] = (
            "🌍 ClimateInsight 使用指南：\n\n"
            "📊 总览 — 点击导航「总览」查看全球气候KPI和图表\n"
            "📈 趋势 — 点击「趋势」查看月度温度变化曲线\n"
            "🏆 排名 — 点击「排名」切换最热/最冷/降水/极端天气排行榜\n"
            "🗺️ 气候带 — 点击「气候带」查看五带分布饼图\n"
            "💬 直接问我 — 如「降水最多的地方？」「各月温度变化？」\n\n"
            "当前支持：全球KPI、月度趋势、4类排名、气候带分布"
        )
        data.pop("limitations", None)

    else:
        data["answer"] = "抱歉，暂不支持该问题。请尝试：最热的站点、月度气温、气候带分布、全球均温。"
        data["intent"] = "unknown"

    return data
