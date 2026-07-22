"""排名与趋势 (均带年份条件和参数校验)"""
from flask import Blueprint, jsonify, request
from db import query_dict
from config import DATA_YEAR

bp = Blueprint("rankings", __name__)

VALID = {"hottest", "coldest", "rainiest", "most_extreme"}
VALID_YEARS = {2022, 2023, 2024}

def _year():
    return request.args.get("year", DATA_YEAR, type=int)

@bp.route("/api/ranking")
def api_ranking():
    cat = request.args.get("category", "hottest")
    limit = request.args.get("limit", 15, type=int)
    y = _year()

    if cat not in VALID:
        return jsonify({"code": 400, "message": f"无效分类: {cat}, 可选: {VALID}"}), 400
    if limit < 1 or limit > 50:
        return jsonify({"code": 400, "message": "limit 必须 1–50"}), 400

    rows = query_dict(
        "SELECT rank_num, station_id, station_name, value FROM ads_ranking WHERE data_year=%s AND category=%s ORDER BY rank_num LIMIT %s",
        (y, cat, limit),
    )
    return jsonify({"code": 0, "message": "ok", "data": rows, "meta": {"data_year": y}})

@bp.route("/api/trend")
def api_trend():
    y = _year()
    rows = query_dict("SELECT obs_month, avg_temp FROM ads_monthly_trend WHERE data_year=%s ORDER BY obs_month", (y,))
    return jsonify({"code": 0, "message": "ok", "data": rows, "meta": {"data_year": y}})

# ── 多年月度趋势 ──
@bp.route("/api/trend/multi-year")
def api_trend_multi_year():
    years_str = request.args.get("years", "2022,2023,2024")
    years = [int(y) for y in years_str.split(",") if int(y) in VALID_YEARS]
    if not years:
        years = [2024]
    rows = query_dict(
        "SELECT data_year as year, obs_month as month, avg_temp, avg_max, avg_min FROM ads_monthly_trend WHERE data_year IN ({}) ORDER BY data_year, obs_month"
        .format(",".join(["%s"] * len(years))),
        tuple(years),
    )
    return jsonify({"code": 0, "message": "ok", "data": rows, "meta": {"years": years}})

# ── 多年气候带分布 ──
@bp.route("/api/zones/multi-year")
def api_zones_multi_year():
    years_str = request.args.get("years", "2022,2023,2024")
    years = [int(y) for y in years_str.split(",") if int(y) in VALID_YEARS]
    if not years:
        years = [2024]
    rows = query_dict(
        "SELECT data_year as year, climate_zone, station_count as cnt FROM ads_zones WHERE data_year IN ({}) ORDER BY data_year, climate_zone"
        .format(",".join(["%s"] * len(years))),
        tuple(years),
    )
    return jsonify({"code": 0, "message": "ok", "data": rows, "meta": {"years": years}})

# ── 气候带详细统计 ──
@bp.route("/api/zones/stats")
def api_zones_stats():
    y = _year()
    rows = query_dict(
        "SELECT climate_zone, COUNT(DISTINCT station_id) as station_count, "
        "ROUND(AVG(avg_temp), 1) as avg_temp, ROUND(AVG(total_precip), 1) as avg_precip, "
        "SUM(extreme_days) as extreme_days, SUM(heat_wave_days) as heat_wave_days, "
        "SUM(cold_wave_days) as cold_wave_days "
        "FROM dws_station_monthly WHERE year=%s GROUP BY climate_zone",
        (y,),
    )
    return jsonify({"code": 0, "message": "ok", "data": rows, "meta": {"data_year": y}})
