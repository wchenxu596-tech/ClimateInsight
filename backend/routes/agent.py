"""Agent API — 受控分析助手"""
from flask import Blueprint, jsonify, request
from agent.service import query as agent_query
from config import DATA_YEAR

bp = Blueprint("agent", __name__)

@bp.route("/api/agent/query", methods=["POST"])
def agent_query_route():
    if not request.is_json:
        return jsonify({"code": 400, "message": "需要JSON请求体"}), 400

    q = (request.json.get("question", "") or "").strip()
    if not q:
        return jsonify({"code": 400, "message": "问题不能为空"}), 400
    if len(q) > 300:
        return jsonify({"code": 400, "message": "问题长度不能超过300字"}), 400

    # 年份校验: 必须在 2010-2025 范围内
    year = request.json.get("year", DATA_YEAR)
    if not isinstance(year, int) or year < 2010 or year > 2025:
        return jsonify({"code": 400, "message": f"仅支持 2010-2025 年数据，收到: {year}"}), 400

    # 拒绝SQL注入
    for kw in ["DROP", "DELETE", "INSERT", "UPDATE", "TRUNCATE", "ALTER", "CREATE", "SELECT", "EXEC", "EXECUTE"]:
        if kw in q.upper():
            return jsonify({"code": 400, "message": "不支持SQL操作，请使用自然语言提问"}), 400

    result = agent_query(q, year)
    return jsonify({"code": 0, "message": "ok", "data": result, "meta": {"data_year": year}})
