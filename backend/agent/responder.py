"""响应生成器 — 模板模式（LLM可选增强）"""
from config import AGENT_ENABLED, DATA_YEAR

ZONE_CN = {"tropical":"热带","temperate":"温带","continental":"大陆性","polar":"寒带","arid":"干旱"}

# 站名中文简表
STATION_CN = {
    "AMUNDSEN SCOTT, AY":"阿蒙森-斯科特站", "ARAFAT, SA":"阿拉法特",
    "VOSTOK, AY":"东方站", "SITEKI, WZ":"锡泰基", "CONCORDIA, AQ":"康科迪亚站",
    "DOME C II, AQ":"冰穹C二号", "MARBLE POINT, AY":"大理石角",
    "MAHABALESHWAR, IN":"默哈伯莱什沃尔", "HONAVAR, IN":"霍纳瓦尔",
    "JOKKMOKK FPL, SW":"约克莫克", "HALLEY, AY":"哈雷站",
    "KHLONG YAI, TH":"空艾", "KAYES DAG DAG, ML":"卡伊",
    "MINA, SA":"米纳", "KOSRAE INTERNATIONAL AIRPORT, FM FM":"科斯雷机场",
    "MATAM OURO SOGUI, SG":"马塔姆", "PREAH VIHEAR, CB":"柏威夏",
    "PODOR, SG":"波多尔", "NARA KEIBANE, ML":"纳拉",
    "YELIMANE, ML":"耶利马内", "LINGUERE, SG":"林盖尔",
    "TAMBACOUNDA, SG":"坦巴昆达", "TILLABERY, NG":"蒂拉贝里",
    "NIORO DU SAHEL, ML":"纽罗", "BERNARD HARBOUR, CA":"伯纳德港",
    "COLVILLE LAKE NWT, CA":"科尔维尔湖", "DAWEI, BM":"土瓦",
    "YE, BM":"耶", "MAO, CD":"马奥", "ZAKATALA, AJ":"扎卡塔拉",
    "GAVAR, AM":"加瓦尔", "FAHUD AUT, MU":"法胡德",
    "BALDRICK AWS, AY":"鲍德里克站", "CAPE PHILLIPS, AY":"菲利普斯角",
    "DOME PLATEAU DOME A, AY":"冰穹A", "DOME PLATEAU EAGLE, AY":"冰穹鹰",
    "HALVFARRYGGEN EP11, AY":"半脊EP11", "LAW DOME SUMMIT, AY":"劳穹顶",
    "MID POINT, AY":"中点站", "PRIESTLEY GLACIER, AY":"普里斯特利冰川",
    "S.A.N.A.E. AWS, AY":"南非科考站", "UNIVERSITY WI ID 8917 SKI BLU, AY":"威大8917站",
    "UNIVERSITY WI ID 8925 LIMBERT AWS, AY":"威大8925站",
    "HALIM PERDANAKUSUMA INTERNATIONAL, ID":"哈利姆机场",
    "KOKONAO TIMUKA, ID":"科科纳奥", "SAM RATULANGI, ID":"萨姆拉图兰吉",
    "SANTO PEKOA INTERNATIONAL, NH":"桑托佩可亚", "OSMANY INTERNATIONAL, BG":"奥斯曼尼机场",
    "MILFORD SOUNDN AWS, NZ":"米尔福德峡湾", "SECRETARY ISLAND AWS, NZ":"秘书岛",
}

def make_response(intent_info: dict, tool_result) -> dict:
    """根据意图和工具结果生成前端可用的回答"""
    intent = intent_info.get("intent", "unknown")
    year = intent_info.get("year", DATA_YEAR)
    data = {"answer": "", "intent": intent, "limitations": [f"数据仅覆盖{year}年，不包含多年对比"]}

    if intent == "kpi":
        data["answer"] = f"{year} 年全球气候核心指标如下："
        data["table"] = {"columns": ["指标", "数值", "单位"], "rows": [
            [r["kpi_desc"], str(r["kpi_value"]), r["kpi_unit"]] for r in tool_result
        ]}

    elif intent == "monthly":
        data["answer"] = f"{year} 年各月平均温度（全球气象站均值）："
        data["chart"] = {
            "type": "line",
            "x": [f"{r['obs_month']}月" for r in tool_result],
            "y": [float(r["avg_temp"]) for r in tool_result],
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

    elif intent == "help":
        data["answer"] = "我可以回答以下问题：\n- 2024年全球平均气温？\n- 最热的10个站点？\n- 各月温度变化？\n- 气候带分布？\n- 降水最多的站点？"

    else:
        data["answer"] = "抱歉，暂不支持该问题。请尝试：最热的站点、月度气温、气候带分布、全球均温。"
        data["intent"] = "unknown"

    return data
