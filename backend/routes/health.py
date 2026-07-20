"""健康检查"""
from flask import Blueprint, jsonify
from db import health as db_health
from config import DATA_YEAR

bp = Blueprint("health", __name__)

@bp.route("/api/health")
def health():
    db_ok = db_health()
    return jsonify({"code": 0, "message": "ok", "data": {
        "status": "healthy" if db_ok else "degraded",
        "database": "connected" if db_ok else "disconnected",
        "data_year": DATA_YEAR
    }}), 200 if db_ok else 503
