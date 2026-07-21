"""ETL 数据质量测试 (需要 MySQL 连接)"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

import pytest
from db import query, query_dict


@pytest.mark.skipif(
    not os.environ.get("MYSQL_PASSWORD"),
    reason="需要 MYSQL_PASSWORD 环境变量"
)
class TestDWSQuality:
    """DWS 层数据质量"""

    def test_primary_key_unique(self):
        """DWS 主键 (station_id, year, obs_month) 无重复"""
        rows = query("""
            SELECT COUNT(*) FROM (
                SELECT station_id, year, obs_month, COUNT(*) AS cnt
                FROM dws_station_monthly WHERE year=2024
                GROUP BY station_id, year, obs_month HAVING cnt > 1
            ) dup
        """)
        assert rows[0][0] == 0, f"DWS 主键重复: {rows[0][0]} 组"

    def test_temperature_range(self):
        """温度在合理范围内"""
        rows = query("""
            SELECT COUNT(*) FROM dws_station_monthly
            WHERE year=2024 AND (avg_temp NOT BETWEEN -90 AND 60)
        """)
        assert rows[0][0] == 0, f"异常温度: {rows[0][0]} 条"

    def test_row_count(self):
        """DWS 行数合理 (13万~15万)"""
        rows = query("SELECT COUNT(*) FROM dws_station_monthly WHERE year=2024")
        cnt = rows[0][0]
        assert 130000 <= cnt <= 150000, f"DWS 行数异常: {cnt}"


@pytest.mark.skipif(
    not os.environ.get("MYSQL_PASSWORD"),
    reason="需要 MYSQL_PASSWORD 环境变量"
)
class TestADSQuality:
    """ADS 层数据质量"""

    def test_monthly_12_records(self):
        """ADS 月度趋势有12条记录"""
        rows = query("SELECT COUNT(*) FROM ads_monthly_trend WHERE data_year=2024")
        assert rows[0][0] == 12, f"月度记录: {rows[0][0]}"

    def test_ranking_15_per_category(self):
        """每个类别有15条排名"""
        for cat in ["hottest", "coldest", "rainiest", "most_extreme"]:
            rows = query(
                "SELECT COUNT(*) FROM ads_ranking WHERE data_year=2024 AND category=%s",
                (cat,)
            )
            assert rows[0][0] == 15, f"{cat} 排名: {rows[0][0]}"

    def test_zones_3_to_6(self):
        """气候带 3~6 类"""
        rows = query("SELECT COUNT(*) FROM ads_zones WHERE data_year=2024")
        cnt = rows[0][0]
        assert 3 <= cnt <= 6, f"气候带数量: {cnt}"

    def test_kpi_values_not_null(self):
        """KPI 值非空"""
        rows = query("SELECT COUNT(*) FROM ads_kpi WHERE data_year=2024 AND kpi_value IS NULL")
        assert rows[0][0] == 0, f"空 KPI: {rows[0][0]}"
