"""
极端天气预警 & 气象站地图 API
"""
from flask import Blueprint, jsonify, request
from db import query_dict
from config import DATA_YEAR
from cache import cached

bp = Blueprint("alert", __name__)

def _year():
    return request.args.get("year", DATA_YEAR, type=int)


@bp.route("/api/alert/risk")
@cached(300)
def api_alert_risk():
    """极端天气风险评分 — 按站聚合，四级预警"""
    y = _year()
    limit = min(request.args.get("limit", 100, type=int), 500)

    rows = list(query_dict("""
        SELECT station_id, station_name, latitude, longitude, climate_zone,
               SUM(heat_wave_days)  AS heat_wave,
               SUM(cold_wave_days)  AS cold_wave,
               SUM(extreme_days)    AS extreme,
               SUM(frost_days)      AS frost,
               SUM(snow_days)       AS snow,
               SUM(thunder_days)    AS thunder,
               ROUND(AVG(avg_temp), 1)   AS avg_temp,
               ROUND(SUM(total_precip), 1) AS total_precip
        FROM dws_station_monthly
        WHERE year = %s
        GROUP BY station_id, station_name, latitude, longitude, climate_zone
    """, (y,)))

    # 计算风险分
    for r in rows:
        r["heat_wave"]  = r["heat_wave"]  or 0
        r["cold_wave"]  = r["cold_wave"]  or 0
        r["extreme"]    = r["extreme"]    or 0
        r["frost"]      = r["frost"]      or 0
        r["snow"]       = r["snow"]       or 0
        r["thunder"]    = r["thunder"]    or 0

        raw = (r["heat_wave"] * 3 + r["cold_wave"] * 3 +
               r["extreme"] * 2 + r["thunder"] + r["frost"] + r["snow"])
        # 归一化到 0-100
        r["risk_score"] = min(round(raw / 10, 1), 100)

        # 预警等级
        if r["risk_score"] >= 60:
            r["alert_level"] = "red"
            r["alert_label"] = "🔴 红色预警"
        elif r["risk_score"] >= 40:
            r["alert_level"] = "orange"
            r["alert_label"] = "🟠 橙色预警"
        elif r["risk_score"] >= 20:
            r["alert_level"] = "yellow"
            r["alert_label"] = "🟡 黄色预警"
        else:
            r["alert_level"] = "blue"
            r["alert_label"] = "🔵 蓝色预警"

    # 按风险分排序
    rows.sort(key=lambda r: r["risk_score"], reverse=True)

    # 统计
    stats = {
        "total_stations": len(rows),
        "red_count":   sum(1 for r in rows if r["alert_level"] == "red"),
        "orange_count": sum(1 for r in rows if r["alert_level"] == "orange"),
        "yellow_count": sum(1 for r in rows if r["alert_level"] == "yellow"),
        "blue_count":  sum(1 for r in rows if r["alert_level"] == "blue"),
        "top_risk":    rows[0]["risk_score"] if rows else 0,
        "top_station": rows[0]["station_name"] if rows else "",
    }

    return jsonify({
        "code": 0,
        "data": {
            "stats": stats,
            "stations": rows[:limit],
        },
        "meta": {"data_year": y},
    })


@bp.route("/api/alert/monthly")
@cached(300)
def api_alert_monthly():
    """月度极端事件聚合（全站）"""
    y = _year()

    rows = query_dict("""
        SELECT obs_month,
               SUM(heat_wave_days) AS heat_wave,
               SUM(cold_wave_days) AS cold_wave,
               SUM(extreme_days)   AS extreme,
               SUM(frost_days)     AS frost,
               SUM(snow_days)      AS snow,
               SUM(thunder_days)   AS thunder,
               COUNT(DISTINCT station_id) AS station_count
        FROM dws_station_monthly
        WHERE year = %s
        GROUP BY obs_month
        ORDER BY obs_month
    """, (y,))

    for r in rows:
        for k in ("heat_wave", "cold_wave", "extreme", "frost", "snow", "thunder"):
            r[k] = r[k] or 0

    return jsonify({"code": 0, "data": rows, "meta": {"data_year": y}})


@bp.route("/api/stations")
@cached(300)
def api_stations():
    """全球气象站概要（用于地图散点）— 使用ADS预聚合表"""
    y = _year()

    rows = query_dict("""
        SELECT station_id, station_name, lat, lon, climate_zone,
               avg_temp, total_precip, risk_events
        FROM ads_stations
        WHERE data_year = %s
    """, (y,))

    return jsonify({
        "code": 0,
        "data": rows,
        "meta": {"data_year": y, "total": len(rows)},
    })


@bp.route("/api/stations/detail")
def api_station_detail():
    """单个气象站月度详情"""
    sid = request.args.get("station_id", "")
    y = _year()

    if not sid:
        return jsonify({"code": 400, "message": "station_id 必填"}), 400

    # 月度明细
    months = query_dict("""
        SELECT obs_month,
               ROUND(avg_temp, 1)     AS avg_temp,
               ROUND(avg_temp_max, 1) AS avg_max,
               ROUND(avg_temp_min, 1) AS avg_min,
               ROUND(max_temp, 1)     AS max_temp,
               ROUND(min_temp, 1)     AS min_temp,
               ROUND(total_precip, 1) AS precip,
               rainy_days, extreme_days,
               heat_wave_days, cold_wave_days,
               frost_days, snow_days, thunder_days,
               obs_days
        FROM dws_station_monthly
        WHERE station_id = %s AND year = %s
        ORDER BY obs_month
    """, (sid, y))

    # 站信息
    info = query_dict("""
        SELECT station_id, station_name,
               ROUND(latitude, 4)  AS lat,
               ROUND(longitude, 4) AS lon,
               climate_zone
        FROM dws_station_monthly
        WHERE station_id = %s AND year = %s
        LIMIT 1
    """, (sid, y))

    # 是否有排名
    ranking = query_dict("""
        SELECT category, rank_num, value
        FROM ads_ranking
        WHERE station_id = %s AND data_year = %s
        ORDER BY category
    """, (sid, y))

    return jsonify({
        "code": 0,
        "data": {
            "info": info[0] if info else None,
            "months": months,
            "rankings": ranking,
        },
        "meta": {"data_year": y},
    })
