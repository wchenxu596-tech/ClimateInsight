"""仪表盘: KPI / 月度趋势 / 气候带 (均带年份条件)"""
from flask import Blueprint, jsonify, request
from db import query_dict
from config import DATA_YEAR
from cache import cached

bp = Blueprint("dashboard", __name__)

def _year():
    return request.args.get("year", DATA_YEAR, type=int)

@bp.route("/api/kpi")
@cached(300)
def api_kpi():
    y = _year()
    rows = query_dict("SELECT kpi_name, kpi_value, kpi_unit, kpi_desc FROM ads_kpi WHERE data_year=%s", (y,))
    return jsonify({"code": 0, "message": "ok", "data": rows, "meta": {"data_year": y}})

@bp.route("/api/monthly")
@cached(300)
def api_monthly():
    y = _year()
    rows = query_dict("SELECT obs_month, avg_temp, avg_max, avg_min FROM ads_monthly_trend WHERE data_year=%s ORDER BY obs_month", (y,))
    return jsonify({"code": 0, "message": "ok", "data": rows, "meta": {"data_year": y}})

@bp.route("/api/zones")
@cached(300)
def api_zones():
    y = _year()
    rows = query_dict("SELECT climate_zone, station_count AS cnt FROM ads_zones WHERE data_year=%s", (y,))
    return jsonify({"code": 0, "message": "ok", "data": rows, "meta": {"data_year": y}})
