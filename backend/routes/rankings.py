"""排名与趋势 (均带年份条件和参数校验)"""
from flask import Blueprint, jsonify, request
from db import query_dict
from config import DATA_YEAR

bp = Blueprint("rankings", __name__)

VALID = {"hottest", "coldest", "rainiest", "most_extreme"}

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
    return jsonify({"code": 0, "message": "仅含2024年月度数据，同比趋势需导入多年数据", "data": rows, "meta": {"data_year": y}})
