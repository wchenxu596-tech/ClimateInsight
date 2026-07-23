"""响应生成器 — 生成丰富的多段落分析 + 图表 + 表格"""
from config import DATA_YEAR

ZONE_CN = {"tropical":"热带","temperate":"温带","continental":"大陆性","polar":"寒带","arid":"干旱"}
MONTH_NAMES = ["1月","2月","3月","4月","5月","6月","7月","8月","9月","10月","11月","12月"]

STATION_CN = {
    "AMUNDSEN SCOTT, AY":"阿蒙森-斯科特站","ARAFAT, SA":"阿拉法特",
    "VOSTOK, AY":"东方站","SITEKI, WZ":"锡泰基","CONCORDIA, AQ":"康科迪亚站",
    "DOME C II, AQ":"冰穹C二号","MARBLE POINT, AY":"大理石角",
    "MAHABALESHWAR, IN":"默哈伯莱什沃尔","HONAVAR, IN":"霍纳瓦尔",
    "JOKKMOKK FPL, SW":"约克莫克","HALLEY, AY":"哈雷站",
    "KHLONG YAI, TH":"空艾","KAYES DAG DAG, ML":"卡伊",
    "MINA, SA":"米纳","KOSRAE INTERNATIONAL AIRPORT, FM FM":"科斯雷机场",
    "MATAM OURO SOGUI, SG":"马塔姆","PREAH VIHEAR, CB":"柏威夏",
    "PODOR, SG":"波多尔","NARA KEIBANE, ML":"纳拉",
    "YELIMANE, ML":"耶利马内","LINGUERE, SG":"林盖尔",
    "TAMBACOUNDA, SG":"坦巴昆达","TILLABERY, NG":"蒂拉贝里",
    "NIORO DU SAHEL, ML":"纽罗","COLVILLE LAKE NWT, CA":"科尔维尔湖",
    "YE, BM":"耶","MAO, CD":"马奥","ZAKATALA, AJ":"扎卡塔拉",
    "GAVAR, AM":"加瓦尔","FAHUD AUT, MU":"法胡德",
    "BALDRICK AWS, AY":"鲍德里克站","DOME PLATEAU DOME A, AY":"冰穹A",
    "MID POINT, AY":"中点站","S.A.N.A.E. AWS, AY":"南非科考站",
}

def _safe(v, default=0):
    try: return float(v)
    except: return default

def _avg(arr):
    valid = [x for x in arr if x is not None]
    return sum(valid) / len(valid) if valid else 0

def _cn_station(name):
    return STATION_CN.get(name, name)


# ═══════════════════════════════════════════
#  响应生成主入口
# ═══════════════════════════════════════════
def make_response(intent_info: dict, tool_result) -> dict:
    intent = intent_info.get("intent", "unknown")
    year = intent_info.get("year", DATA_YEAR)
    data = {"answer": "", "intent": intent}

    try:
        if intent == "kpi":
            _handle_kpi(data, tool_result, year)
        elif intent == "monthly":
            _handle_monthly(data, tool_result, year, intent_info)
        elif intent == "ranking":
            _handle_ranking(data, tool_result, year, intent_info)
        elif intent == "zones":
            _handle_zones(data, tool_result, year)
        elif intent == "compare":
            _handle_compare(data, tool_result, intent_info)
        elif intent == "trend_analysis":
            _handle_trend_analysis(data, tool_result, intent_info)
        elif intent == "seasonal":
            _handle_seasonal(data, tool_result, year)
        elif intent == "zone_detail":
            _handle_zone_detail(data, tool_result, year)
        elif intent == "extremes":
            _handle_extremes(data, tool_result, year)
        elif intent == "station_query":
            _handle_station_query(data, tool_result, year, intent_info)
        elif intent == "page_analysis":
            _handle_page_analysis(data, tool_result, year, intent_info)
        elif intent == "chat":
            _handle_chat(data)
        elif intent == "help":
            _handle_help(data)
        else:
            data["answer"] = "抱歉，暂不支持该问题。请尝试：最热的站点、月度气温、气候带分布、全球均温、多年趋势分析。"
            data["intent"] = "unknown"
    except Exception as e:
        data["answer"] = f"生成回答时出错: {str(e)[:80]}"

    return data


# ═══════════════════════════════════════════
#  各意图处理函数
# ═══════════════════════════════════════════

def _handle_kpi(data, rows, year):
    lines = [f"📊 {year} 年全球气候核心指标"]
    table_rows = []
    for r in rows:
        name = r.get("kpi_desc", r["kpi_name"])
        val = f"{r['kpi_value']}{r.get('kpi_unit','')}"
        table_rows.append([name, val, r.get("kpi_unit","")])
        lines.append(f"• {name}：{val}")
    data["answer"] = "\n".join(lines)
    data["table"] = {"columns": ["指标","数值","单位"], "rows": table_rows}

def _handle_monthly(data, rows, year, info):
    months_filter = info.get("months")
    if months_filter:
        rows = [r for r in rows if r["obs_month"] in months_filter]
        mo_range = f"{months_filter[0]}~{months_filter[-1]}月"
        data["answer"] = f"📈 {year} 年 {mo_range} 全球均温变化"
    else:
        data["answer"] = f"📈 {year} 年各月全球均温变化"

    temps = [_safe(r["avg_temp"]) for r in rows]
    warmest = max(range(len(temps)), key=lambda i: temps[i]) if temps else 0
    coldest = min(range(len(temps)), key=lambda i: temps[i]) if temps else 0
    avg_all = _avg(temps)

    data["answer"] += f"\n\n全年均温 {avg_all:.1f}°C，最暖为{rows[warmest]['obs_month']}月（{temps[warmest]:.1f}°C），最冷为{rows[coldest]['obs_month']}月（{temps[coldest]:.1f}°C）。年温差振幅 {temps[warmest]-temps[coldest]:.1f}°C。"

    data["chart"] = {
        "type":"line",
        "x":[f"{r['obs_month']}月" for r in rows],
        "y":[float(r["avg_temp"]) for r in rows],
        "name":"均温(°C)"
    }

def _handle_ranking(data, rows, year, info):
    cat = info.get("category","hottest")
    names = {"hottest":"最高温","coldest":"最低温","rainiest":"降水量","most_extreme":"极端天数"}
    unit = "°C" if cat in ("hottest","coldest") else ("mm" if cat=="rainiest" else "天")
    cname = names.get(cat, cat)

    data["answer"] = f"🏆 {year} 年{cname}站点排名 TOP{len(rows)}"
    table_rows = []
    for r in rows:
        st_name = _cn_station(r["station_name"])
        table_rows.append([str(r["rank_num"]), st_name, f"{r['value']}{unit}"])

    if rows:
        top1 = _cn_station(rows[0]["station_name"])
        data["answer"] += f"\n\n榜首为「{top1}」，{cname}达 {rows[0]['value']}{unit}。"
        if len(rows) >= 2:
            data["answer"] += f"第二名「{_cn_station(rows[1]['station_name'])}」{rows[1]['value']}{unit}，"
            gap = _safe(rows[0]["value"]) - _safe(rows[1]["value"])
            data["answer"] += f"与榜首差距 {gap:.1f}{unit}。"

    data["table"] = {"columns":["排名","站点",f"{cname}({unit})"], "rows":table_rows}
    data["chart"] = {"type":"bar",
        "x":[_cn_station(r["station_name"])[:10] for r in rows],
        "y":[float(r["value"]) for r in rows],
        "name":f"{cname}({unit})"}

def _handle_zones(data, rows, year):
    total = sum(r["cnt"] for r in rows)
    data["answer"] = f"🌍 {year} 年全球气候带分布（共 {total} 站）"
    table_rows = []
    for r in rows:
        zone = ZONE_CN.get(r["climate_zone"], r["climate_zone"])
        pct = (r["cnt"]/total*100) if total else 0
        table_rows.append([zone, str(r["cnt"]), f"{pct:.1f}%"])
        data["answer"] += f"\n• {zone}：{r['cnt']} 站（{pct:.1f}%）"
    # 找最大
    if rows:
        largest = max(rows, key=lambda r: r["cnt"])
        data["answer"] += f"\n\n{ZONE_CN.get(largest['climate_zone'],largest['climate_zone'])}站点最多，占主导地位。"

    data["table"] = {"columns":["气候带","站点数","占比"], "rows":table_rows}
    data["chart"] = {"type":"pie",
        "x":[ZONE_CN.get(r["climate_zone"],r["climate_zone"]) for r in rows],
        "y":[int(r["cnt"]) for r in rows],
        "name":"站点数"}

def _handle_compare(data, results, info):
    years = info.get("years",[])
    compare_type = info.get("type","kpi")
    if not years:
        data["answer"] = "请指定需要对比的年份。"
        return

    data["answer"] = f"📊 多年对比（{', '.join(str(y) for y in years)}）"
    temps = {}
    for y, rows in results.items():
        for r in rows:
            if r.get("kpi_name") == "global_avg_temp":
                temps[y] = _safe(r.get("kpi_value"))

    lines = [f"• {y} 年全球年均温：{temps.get(y,'--'):.2f}°C" if isinstance(temps.get(y),(int,float)) else f"• {y} 年：{temps.get(y,'--')}" for y in years]
    data["answer"] += "\n" + "\n".join(lines)

    valid = {y: v for y, v in temps.items() if isinstance(v,(int,float))}
    if len(valid) >= 2:
        warmest_y = max(valid, key=valid.get)
        coldest_y = min(valid, key=valid.get)
        diff = valid[warmest_y] - valid[coldest_y]
        data["answer"] += f"\n\n{warmest_y} 年最暖（{valid[warmest_y]:.2f}°C），{coldest_y} 年最冷（{valid[coldest_y]:.2f}°C），两年温差 {diff:.2f}°C。"

    data["chart"] = {"type":"bar",
        "x":[f"{y}年" for y in years],
        "y":[float(valid.get(y,0)) for y in years],
        "name":"年均温(°C)"}

def _handle_trend_analysis(data, result, info):
    years = info.get("years", [2015, 2025])
    trend = result.get("trend", {})
    kpi = result.get("kpi", {})

    lines = [f"🌡️ {years[0]}–{years[-1]} 年全球温度趋势分析\n"]

    # 计算逐年均温
    yearly_avg = {}
    for y in sorted(trend.keys()):
        rows = trend[y]
        temps = [_safe(r["avg_temp"]) for r in rows]
        if temps:
            yearly_avg[y] = _avg(temps)

    if len(yearly_avg) >= 2:
        y_list = sorted(yearly_avg.keys())
        first_y, last_y = y_list[0], y_list[-1]
        change = yearly_avg[last_y] - yearly_avg[first_y]
        rate = (change / (last_y - first_y)) * 10 if last_y > first_y else 0

        lines.append(f"📈 总体趋势：{first_y} 年全球年均温 {yearly_avg[first_y]:.1f}°C，{last_y} 年升至 {yearly_avg[last_y]:.1f}°C。")
        direction = "上升" if change > 0 else "下降"
        lines.append(f"累计{direction} {abs(change):.2f}°C，变暖速率约 {rate:.2f}°C/十年。")

        warmest_y = max(yearly_avg, key=yearly_avg.get)
        coldest_y = min(yearly_avg, key=yearly_avg.get)
        lines.append(f"\n🔍 极值：最暖年份 {warmest_y} 年（{yearly_avg[warmest_y]:.1f}°C），最冷年份 {coldest_y} 年（{yearly_avg[coldest_y]:.1f}°C）。")

        # 前后半段对比
        mid = len(y_list) // 2
        early = _avg([yearly_avg[y] for y in y_list[:mid]])
        late = _avg([yearly_avg[y] for y in y_list[mid:]])
        lines.append(f"\n📊 阶段对比：前半段均温 {early:.2f}°C，后半段 {late:.2f}°C，后半段偏高 {late-early:.2f}°C。")

        if change > 0.3:
            lines.append(f"\n⚠️ 结论：该时段升温幅度显著，超过自然变率范围，与全球温室气体排放趋势一致。极端高温事件频率可能随之增加。")
        else:
            lines.append(f"\n💡 结论：温度变化在正常波动范围内，但仍需持续关注长期趋势。")

    if kpi:
        # 取最近一年的极端事件占比
        last_kpi_year = max(kpi.keys())
        for r in kpi[last_kpi_year]:
            if r.get("kpi_name") == "extreme_event_pct":
                lines.append(f"\n📋 {last_kpi_year} 年极端事件占比：{r['kpi_value']}%")

    data["answer"] = "\n".join(lines)

def _handle_seasonal(data, result, year):
    trend = result.get("trend", {})
    years_list = result.get("years", [])
    if not trend:
        data["answer"] = "暂无季节分析数据。"
        return

    seasons = {"春季": [3,4,5], "夏季": [6,7,8], "秋季": [9,10,11], "冬季": [12,1,2]}
    season_avgs = {s: [] for s in seasons}

    for y in sorted(trend.keys()):
        rows = trend[y]
        for sname, months in seasons.items():
            temps = [_safe(r["avg_temp"]) for r in rows if r.get("month") in months or r.get("obs_month") in months]
            if temps: season_avgs[sname].append((y, _avg(temps)))

    lines = [f"🌡️ 四季温度分析（截至 {year} 年）\n"]
    for sname in seasons:
        vals = season_avgs[sname]
        if len(vals) >= 2:
            first, last = vals[0], vals[-1]
            diff = last[1] - first[1]
            d = "升温" if diff > 0 else "降温"
            lines.append(f"• {sname}：{first[0]}年 {first[1]:.1f}°C → {last[0]}年 {last[1]:.1f}°C（{d} {abs(diff):.1f}°C）")

    # 找变化最大的季节
    changes = []
    for sname in seasons:
        vals = season_avgs[sname]
        if len(vals) >= 2:
            changes.append((sname, vals[-1][1] - vals[0][1]))
    if changes:
        fastest = max(changes, key=lambda x: abs(x[1]))
        lines.append(f"\n⚠️ {fastest[0]}变化最为显著（{fastest[1]:+.1f}°C），")
        if fastest[0] == "冬季":
            lines.append("冬季变暖可能导致降雪减少、冰川退缩。")
        elif fastest[0] == "夏季":
            lines.append("夏季升温加剧热浪和干旱风险。")
        else:
            lines.append("季节温度变化正在影响生态系统节律。")

    data["answer"] = "\n".join(lines)

def _handle_zone_detail(data, result, year):
    zones_data = result.get("zones", {})
    years_list = result.get("years", [])
    if not zones_data:
        data["answer"] = "暂无气候带趋势数据。"
        return

    lines = [f"🌍 各气候带温度变化趋势\n"]
    zone_temps = {}

    for y in sorted(zones_data.keys()):
        for r in zones_data[y]:
            zone = ZONE_CN.get(r.get("climate_zone",""), r.get("climate_zone",""))
            if zone not in zone_temps:
                zone_temps[zone] = []
            t = _safe(r.get("avg_temp"))
            if t: zone_temps[zone].append((y, t))

    for zone, vals in sorted(zone_temps.items()):
        if len(vals) >= 2:
            first, last = vals[0], vals[-1]
            diff = last[1] - first[1]
            lines.append(f"• {zone}：{first[0]}年 {first[1]:.1f}°C → {last[0]}年 {last[1]:.1f}°C（{diff:+.1f}°C）")

    # 升温最快
    changes = [(z, v[-1][1]-v[0][1]) for z, v in zone_temps.items() if len(v) >= 2]
    if changes:
        fastest = max(changes, key=lambda x: abs(x[1]))
        lines.append(f"\n🔥 升温最快的是{fastest[0]}（{fastest[1]:+.1f}°C），反映了全球变暖在高纬度/高海拔地区的放大效应。")
        if fastest[0] == "寒带":
            lines.append("寒带升温可能加速永久冻土融化和海冰退缩。")

    data["answer"] = "\n".join(lines)

def _handle_extremes(data, result, year):
    zones_data = result.get("zones", {})
    if not zones_data:
        data["answer"] = "暂无极端事件趋势数据。"
        return

    lines = [f"⚠️ 极端天气事件趋势分析\n"]
    zone_extremes = {}
    for y in sorted(zones_data.keys()):
        for r in zones_data[y]:
            zone = ZONE_CN.get(r.get("climate_zone",""), r.get("climate_zone",""))
            total = (_safe(r.get("extreme_days")) + _safe(r.get("heat_wave_days")) + _safe(r.get("cold_wave_days")))
            if zone not in zone_extremes:
                zone_extremes[zone] = []
            zone_extremes[zone].append((y, total))

    for zone, vals in sorted(zone_extremes.items()):
        if len(vals) >= 2:
            first, last = vals[0], vals[-1]
            diff = last[1] - first[1]
            trend = "增加" if diff > 0 else "减少"
            lines.append(f"• {zone}：极端事件从 {first[1]:.0f} 天次 → {last[1]:.0f} 天次（{trend} {abs(diff):.0f}）")

    total_change = sum(v[-1][1]-v[0][1] for v in zone_extremes.values() if len(v) >= 2)
    if total_change > 0:
        lines.append(f"\n⚠️ 总体极端事件呈增加趋势（+{total_change:.0f} 天次），与全球气候变暖背景一致。")
    lines.append("\n极端高温事件主要集中在热带和温带地区，寒潮事件以寒带和大陆性气候带为主。")

    data["answer"] = "\n".join(lines)

def _handle_station_query(data, result, year, info):
    detail = result.get("detail", {})
    info_data = detail.get("info")
    months = detail.get("months", [])

    if not info_data:
        st = info.get("station","")
        data["answer"] = f"未找到「{st}」的数据。请尝试使用站点英文名或ID查询（如 'VOSTOK' 或 'AMUNDSEN SCOTT'）。"
        return

    name = _cn_station(info_data.get("station_name",""))
    zone = ZONE_CN.get(info_data.get("climate_zone",""), "")
    lat, lon = info_data.get("lat",0), info_data.get("lon",0)

    lines = [f"📍 {name} — {year} 年数据"]
    if zone: lines.append(f"气候带：{zone}  |  坐标：{lat:.2f}°N, {lon:.2f}°E")

    if months:
        temps = [_safe(m.get("avg_temp")) for m in months]
        precips = [_safe(m.get("precip")) for m in months]
        extremes = sum(_safe(m.get("extreme_days")) for m in months)
        heat = sum(_safe(m.get("heat_wave_days")) for m in months)
        cold = sum(_safe(m.get("cold_wave_days")) for m in months)
        obs = sum(_safe(m.get("obs_days")) for m in months)
        valid_temps = [t for t in temps if t != 0]
        avg_t = _avg(valid_temps) if valid_temps else 0
        max_t = max(temps) if temps else 0
        min_t = min(valid_temps) if valid_temps else 0
        total_p = sum(precips)

        lines.append(f"\n📊 年均温：{avg_t:.1f}°C（最高 {max_t:.1f}°C / 最低 {min_t:.1f}°C）")
        lines.append(f"🌧️ 年降水：{total_p:.1f}mm")
        lines.append(f"⚠️ 极端事件：极端 {extremes}天 + 热浪 {heat}天 + 寒潮 {cold}天")
        lines.append(f"📋 有效观测：{obs} 天")

    data["answer"] = "\n".join(lines)

    if months:
        data["chart"] = {"type":"line",
            "x":[f"{m['obs_month']}月" for m in months],
            "y":[float(m.get("avg_temp",0) or 0) for m in months],
            "name":"均温(°C)"}

def _handle_page_analysis(data, result, year, info):
    page = info.get("page","") or result.get("page","总览")
    page_names = {"总览":"全球总览","dashboard":"全球总览","趋势":"温度趋势","trend":"温度趋势",
                  "排名":"站点排名","ranking":"站点排名","气候带":"气候带分布","zones":"气候带分布",
                  "地图":"全球地图","map":"全球地图","预警":"极端预警","alert":"极端预警"}
    page_name = page_names.get(page, page)
    years_ctx = result.get("years_context", [year])
    lines = [f"📊 「{page_name}」综合分析（{year} 年）\n"]

    # ── KPI ──
    kpi_data = result.get("kpi")
    if isinstance(kpi_data, list) and kpi_data:
        lines.append("📋 核心指标")
        kpi_map = {}
        for r in kpi_data:
            name = r.get("kpi_desc", r.get("kpi_name",""))
            val = f"{r.get('kpi_value','')}{r.get('kpi_unit','')}"
            kpi_map[r.get("kpi_name","")] = (name, val)
            lines.append(f"• {name}：{val}")

    # ── KPI 历史趋势 ──
    kpi_hist = result.get("kpi_history")
    if isinstance(kpi_hist, dict) and len(kpi_hist) >= 2:
        lines.append(f"\n📈 多年趋势（{years_ctx[0]}-{years_ctx[-1]}）")
        for y in sorted(kpi_hist.keys()):
            for r in kpi_hist[y]:
                if r.get("kpi_name") == "global_avg_temp":
                    t = _safe(r.get("kpi_value"))
                    lines.append(f"• {y}年 均温 {t:.1f}°C")
        # 计算变化
        y_list = sorted(kpi_hist.keys())
        if len(y_list) >= 2:
            first_t = _safe(next((r.get("kpi_value") for r in kpi_hist[y_list[0]] if r.get("kpi_name")=="global_avg_temp"), None))
            last_t = _safe(next((r.get("kpi_value") for r in kpi_hist[y_list[-1]] if r.get("kpi_name")=="global_avg_temp"), None))
            if first_t and last_t:
                change = last_t - first_t
                lines.append(f"累计变化：{change:+.1f}°C（{abs(change/len(y_list)*10):.2f}°C/十年）")

    # ── 月度 ──
    monthly = result.get("monthly")
    if isinstance(monthly, list) and monthly:
        temps = [_safe(r.get("avg_temp",r.get("avg",0))) for r in monthly]
        valid_t = [t for t in temps if t]
        if valid_t:
            warmest_i = max(range(len(temps)), key=lambda i: temps[i] if temps[i] else -99)
            lines.append(f"\n🌡️ 月度温度")
            lines.append(f"年均温 {_avg(valid_t):.1f}°C，最暖 {MONTH_NAMES[warmest_i]}（{temps[warmest_i]:.1f}°C），最冷 {MONTH_NAMES[min(range(len(valid_t)),key=lambda i:valid_t[i])]}（{min(valid_t):.1f}°C）")

    # ── 气候带 ──
    zones = result.get("zones")
    if isinstance(zones, list) and zones:
        total = sum(r.get("cnt",0) for r in zones)
        if total > 0:
            largest = max(zones, key=lambda r: r.get("cnt",0))
            lines.append(f"\n🌍 气候带（共 {total} 站）")
            lines.append(f"最大：{ZONE_CN.get(largest.get('climate_zone',''),'--')}（{largest.get('cnt',0)}站，{largest.get('cnt',0)/total*100:.0f}%）")
            for r in zones:
                lines.append(f"• {ZONE_CN.get(r.get('climate_zone',''),r.get('climate_zone',''))}：{r.get('cnt',0)}站")

    # ── 气候带趋势 ──
    zones_trend = result.get("zones_trend")
    if isinstance(zones_trend, dict) and len(zones_trend) >= 2:
        zone_changes = {}
        for y in sorted(zones_trend.keys()):
            for r in zones_trend[y]:
                z = ZONE_CN.get(r.get("climate_zone",""),"")
                if z not in zone_changes: zone_changes[z] = []
                zone_changes[z].append((y, _safe(r.get("avg_temp"))))
        if zone_changes:
            lines.append(f"\n🔥 气候带温度变化")
            for z, vals in zone_changes.items():
                if len(vals) >= 2:
                    diff = vals[-1][1] - vals[0][1]
                    lines.append(f"• {z}：{vals[0][0]}年 {vals[0][1]:.1f}°C → {vals[-1][0]}年 {vals[-1][1]:.1f}°C（{diff:+.1f}°C）")
            fastest = max(zone_changes.items(), key=lambda x: x[1][-1][1]-x[1][0][1] if len(x[1])>=2 else 0)
            if len(fastest[1]) >= 2:
                lines.append(f"升温最快：{fastest[0]}（{fastest[1][-1][1]-fastest[1][0][1]:+.1f}°C）")

    # ── 排名 ──
    for cat_key, cat_label in [("hottest","🔥 最高温"), ("coldest","❄️ 最低温"), ("rainiest","🌧️ 降水"), ("extremes","⚠️ 极端")]:
        ranking = result.get(cat_key) or result.get("extremes_ranking" if cat_key == "extremes" else "")
        if isinstance(ranking, list) and ranking:
            lines.append(f"\n{cat_label} TOP{len(ranking)}")
            for r in ranking[:5]:
                st = _cn_station(r.get("station_name",""))
                lines.append(f"• {st}：{r.get('value','')} {('°C' if cat_key in ('hottest','coldest') else 'mm' if cat_key=='rainiest' else '天')}")

    lines.append(f"\n💡 可继续提问：「{years_ctx[0]}和{years_ctx[-1]}哪个更热？」「极端事件变化趋势？」「最热的站点？」")
    data["answer"] = "\n".join(lines)

def _handle_chat(data):
    data["answer"] = (
        "👋 你好！我是 ClimateInsight 气候智能分析助手。\n\n"
        "🌍 我可以帮你分析 NOAA GSOD 全球气候数据（2015-2025）：\n\n"
        "📊 数据查询：\n"
        "• 「全球平均气温？」— KPI 核心指标\n"
        "• 「各月温度变化？」— 月度温度趋势\n"
        "• 「最热的5个站点？」— 排名查询\n"
        "• 「气候带分布？」— 五带分布\n\n"
        "📈 趋势分析：\n"
        "• 「这些年变暖了多少？」— 多年趋势\n"
        "• 「哪个季节最热？」— 季节分析\n"
        "• 「气候带温度变化？」— 气候带趋势\n"
        "• 「极端事件增加了吗？」— 极端趋势\n\n"
        "📋 页面分析：\n"
        "• 「分析当前页面」— 解读你正在看的图表\n\n"
        "直接输入问题即可！"
    )

def _handle_help(data):
    data["answer"] = (
        "🌍 ClimateInsight 使用指南\n\n"
        "📱 导航（右侧）：\n"
        "• 🗺️ 地图 — 全球气象站分布，支持按气候带/大洲筛选\n"
        "• 📊 总览 — 年度KPI + 月度趋势 + 排名\n"
        "• 📈 趋势 — 多年温度演变 + 距平热力图\n"
        "• 🌍 气候带 — 各气候带站点数 + 温度变化\n"
        "• 🏆 排名 — 四类排名 2×2 网格\n"
        "• ⚠️ 预警 — 极端事件风险分级\n\n"
        "🕐 左侧年份选择器切换不同年份\n"
        "💬 AI 面板点击右侧「🌿 AI」按钮打开\n\n"
        "你可以直接问我任何气候相关问题！"
    )
