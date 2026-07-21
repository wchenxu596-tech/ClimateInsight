"""API 端点测试 (需要后端运行)"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

import pytest
from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


class TestHealthEndpoint:
    """健康检查"""

    def test_health_returns_json(self, client):
        r = client.get("/api/health")
        assert r.status_code in (200, 503)
        data = r.get_json()
        assert "code" in data
        assert "data" in data
        assert "status" in data["data"]

    def test_health_has_data_year(self, client):
        r = client.get("/api/health")
        data = r.get_json()
        assert "data_year" in data["data"]


class TestDashboardEndpoints:
    """看板API"""

    def test_kpi_accepts_year(self, client):
        r = client.get("/api/kpi?year=2024")
        assert r.status_code == 200
        data = r.get_json()
        assert data["code"] == 0

    def test_monthly_accepts_year(self, client):
        r = client.get("/api/monthly?year=2024")
        assert r.status_code == 200
        data = r.get_json()
        assert data["code"] == 0

    def test_zones_accepts_year(self, client):
        r = client.get("/api/zones?year=2024")
        assert r.status_code == 200
        data = r.get_json()
        assert data["code"] == 0


class TestRankingEndpoint:
    """排名API参数校验"""

    def test_valid_category(self, client):
        for cat in ["hottest", "coldest", "rainiest", "most_extreme"]:
            r = client.get(f"/api/ranking?year=2024&category={cat}")
            assert r.status_code == 200, f"category={cat} 应返回200"

    def test_invalid_category_returns_400(self, client):
        r = client.get("/api/ranking?year=2024&category=invalid")
        assert r.status_code == 400

    def test_limit_too_high_returns_400(self, client):
        r = client.get("/api/ranking?year=2024&category=hottest&limit=100")
        assert r.status_code == 400

    def test_limit_negative_returns_400(self, client):
        r = client.get("/api/ranking?year=2024&category=hottest&limit=-1")
        assert r.status_code == 400


class TestAgentEndpoint:
    """Agent API"""

    def test_empty_question_returns_400(self, client):
        r = client.post("/api/agent/query", json={"question": ""})
        assert r.status_code == 400

    def test_missing_json_returns_400(self, client):
        r = client.post("/api/agent/query", data="not json")
        assert r.status_code == 400

    def test_too_long_question_returns_400(self, client):
        r = client.post("/api/agent/query", json={"question": "x" * 301})
        assert r.status_code == 400

    def test_sql_keyword_rejected(self, client):
        r = client.post("/api/agent/query", json={"question": "DROP TABLE", "year": 2024})
        assert r.status_code == 400

    def test_invalid_year_rejected(self, client):
        r = client.post("/api/agent/query", json={"question": "全球均温", "year": 2023})
        assert r.status_code == 400

    def test_non_int_year_rejected(self, client):
        r = client.post("/api/agent/query", json={"question": "全球均温", "year": "2024"})
        assert r.status_code == 400  # 字符串年份应被拒绝

    def test_valid_query_returns_200(self, client):
        r = client.post("/api/agent/query", json={"question": "2024年全球平均气温？", "year": 2024})
        assert r.status_code == 200
        data = r.get_json()
        assert data["code"] == 0
        assert "data" in data
        assert "meta" in data
