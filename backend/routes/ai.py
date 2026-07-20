"""AI 对话接口（占位）"""
from flask import Blueprint, jsonify, request

bp = Blueprint("ai", __name__)

@bp.route("/api/nl2sql", methods=["POST"])
def api_nl2sql():
    q = request.json.get("question", "") if request.is_json else ""
    return jsonify({
        "code": 0, "message": "NL2SQL 功能将在接入大模型后开放",
        "data": {"question": q, "explanation": "当前版本仅支持预设看板查询。请使用导航栏查看：总览、趋势、排名、气候带。"}
    })
