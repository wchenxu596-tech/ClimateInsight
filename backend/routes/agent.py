"""Agent API — 受控分析助手 (v1 兼容 + v2 新增)"""
from flask import Blueprint, jsonify, request
from agent.service import query as agent_query
from agent.schemas import AnalysisPlan, validate_plan
from agent.planner import create_plan
from agent.catalog import DATASETS
from config import DATA_YEAR, AGENT_ENABLED

bp = Blueprint("agent", __name__)

PAGE_MAP = {"map":"地图","dashboard":"总览","trend":"趋势","ranking":"排名","zones":"气候带","alert":"预警"}

# ═══════════════ v1: 兼容旧 POST /api/agent/query ═══════════════
@bp.route("/api/agent/query", methods=["POST"])
def agent_query_route():
    if not request.is_json:
        return jsonify({"code": 400, "message": "需要JSON请求体"}), 400

    q = (request.json.get("question", "") or "").strip()
    if not q:
        return jsonify({"code": 400, "message": "问题不能为空"}), 400
    if len(q) > 500:
        return jsonify({"code": 400, "message": "问题长度不能超过500字"}), 400

    year = request.json.get("year", DATA_YEAR)
    if not isinstance(year, int) or year not in range(2015, 2026):
        return jsonify({"code": 400, "message": f"仅支持 2015-2025 年数据，收到: {year}"}), 400

    raw_page = request.json.get("page", "")
    page = PAGE_MAP.get(raw_page, raw_page)

    for kw in ["DROP", "DELETE", "INSERT", "UPDATE", "TRUNCATE", "ALTER", "CREATE", "SELECT", "EXEC", "EXECUTE"]:
        if kw in q.upper():
            return jsonify({"code": 400, "message": "不支持SQL操作"}), 400

    result = agent_query(q, year, page)
    return jsonify({"code": 0, "message": "ok", "data": result, "meta": {"data_year": year}})


# ═══════════════ v2: 高级分析 API ═══════════════

@bp.route("/api/v2/analysis/plan", methods=["POST"])
def analysis_plan_preview():
    """仅解析/预览 AnalysisPlan，供用户确认（手册 6.1）"""
    if not request.is_json:
        return jsonify({"code":400,"message":"需要JSON请求体"}), 400

    q = (request.json.get("question","") or "").strip()
    if not q or len(q) > 500:
        return jsonify({"code":400,"message":"问题1-500字"}), 400

    plan = create_plan(q)
    return jsonify({
        "code": 0,
        "data": {
            "plan": plan.to_dict(),
            "source": plan.source,
            "confidence": plan.confidence
        }
    })


@bp.route("/api/v2/analysis/runs", methods=["POST"])
def analysis_run():
    """执行高级分析（同步或返回 job_id）"""
    if not request.is_json:
        return jsonify({"code":400,"message":"需要JSON请求体"}), 400

    # 接受自然语言或结构化 Plan
    if "plan" in request.json:
        plan_dict = request.json["plan"]
        plan, errors = validate_plan(plan_dict)
        if errors:
            return jsonify({"code":400,"message":"无效计划","errors":errors}), 400
    elif "question" in request.json:
        q = request.json["question"].strip()
        plan = create_plan(q)
    else:
        return jsonify({"code":400,"message":"需要 question 或 plan"}), 400

    year = request.json.get("year", DATA_YEAR)
    page = PAGE_MAP.get(request.json.get("page",""), "")

    try:
        # 轻量查询同步返回
        if plan.granularity == "year" and len(plan.time_groups) <= 2:
            result = _execute_plan(plan, year, page)
            result["run_id"] = f"run_{hash(plan.raw_question) & 0xFFFFF:05x}"
            result["status"] = "completed"
            return jsonify({"code":0,"data":result})
        else:
            # 复杂查询返回 job_id（后续 Celery 实现）
            return jsonify({
                "code":0,
                "data":{
                    "job_id": f"job_{hash(plan.raw_question) & 0xFFFFF:05x}",
                    "status":"queued",
                    "plan":plan.to_dict(),
                    "message":"复杂查询已加入队列。异步报告功能即将上线。"
                }
            })
    except Exception as e:
        return jsonify({"code":500,"message":f"分析失败: {str(e)[:100]}"}), 500


def _execute_plan(plan: AnalysisPlan, year: int, page: str) -> dict:
    """执行轻量 AnalysisPlan → 同步返回结果"""
    # 当前轻量实现：委托给 service.query 兼容层
    q = plan.raw_question or f"分析{plan.time_groups[0].label if plan.time_groups else year}年数据"
    legacy_result = agent_query(q, year, page)

    return {
        "plan": plan.to_dict(),
        "summary": legacy_result.get("answer",""),
        "tables": [legacy_result["table"]] if legacy_result.get("table") else [],
        "charts": [{"spec": legacy_result["chart"]}] if legacy_result.get("chart") else [],
        "statistics": [],
        "alerts": [],
        "suggestions": [],
        "lineage": [{"step":"legacy_query","source":plan.source}],
        "limitations": legacy_result.get("limitations",[]),
        "meta": {"data_version":"v46","timing_ms":{}}
    }


@bp.route("/api/v2/catalog", methods=["GET"])
def catalog_info():
    """返回可用数据集、字段、聚合白名单（供前端和 LLM 使用）"""
    return jsonify({
        "code": 0,
        "data": {
            "datasets": {k: {"desc": v["description"], "granularity": v["granularity"],
                             "year_range": v["year_range"], "columns": list(v["columns"].keys())}
                        for k, v in DATASETS.items()},
            "aggregations": list({"mean","sum","min","max","count","std"}),
            "climate_zones": list({"tropical","temperate","arid","continental","polar"}),
        }
    })
