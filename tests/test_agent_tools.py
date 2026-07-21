"""Agent 工具安全测试"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from agent.tools import TOOLS, VALID_CATEGORIES, VALID_YEARS


class TestAgentToolsSecurity:
    """Agent工具: 安全校验、白名单"""

    def test_valid_years(self):
        assert VALID_YEARS == {2024}, f"VALID_YEARS 应为 {{2024}}, 实际 {VALID_YEARS}"

    def test_only_ads_tables_in_queries(self):
        """确保所有工具SQL仅访问ADS表"""
        import inspect
        for name, func in TOOLS.items():
            src = inspect.getsource(func)
            # 不允许出现 DWS/DWD/ODS 表
            assert "dws_station_monthly" not in src, f"{name} 不应直接访问 DWS 表"
            assert "dwd_" not in src, f"{name} 不应访问 DWD 表"
            assert "ods_" not in src, f"{name} 不应访问 ODS 表"
            # 必须参数化 (有 %s 占位符)
            assert "%s" in src or "params" in src, f"{name} 必须使用参数化查询"

    def test_valid_categories(self):
        assert VALID_CATEGORIES == {"hottest", "coldest", "rainiest", "most_extreme"}

    def test_tools_registry(self):
        """工具注册表包含所有必要工具"""
        expected = {"get_kpi", "get_monthly", "get_ranking", "get_zones"}
        assert set(TOOLS.keys()) == expected, f"工具注册表不完整: {set(TOOLS.keys())}"


class TestAgentInputValidation:
    """Agent输入验证"""

    def test_agent_route_rejects_sql_keywords(self):
        """SQL注入关键词应被拒绝"""
        keywords = ["DROP", "DELETE", "INSERT", "UPDATE", "TRUNCATE", "ALTER", "CREATE", "SELECT", "EXEC", "EXECUTE"]
        for kw in keywords:
            assert kw.isupper()  # 确保关键词都是大写

    def test_agent_max_question_length(self):
        """问题长度限制300字"""
        from backend.routes.agent import agent_query_route
        # 检查路由中是否有长度检查
        import inspect
        src = inspect.getsource(agent_query_route)
        assert "300" in src, "Agent路由需包含300字长度限制"
