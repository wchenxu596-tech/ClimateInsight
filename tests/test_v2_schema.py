"""Phase 7: Schema / TimeGroup / SpatialFilter 单元测试"""
import pytest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
from agent.schemas import AnalysisPlan, TimeGroup, SpatialFilter, validate_plan

class TestTimeGroup:
    def test_valid(self):
        t = TimeGroup(start=2015, end=2020, label="base")
        assert t.start == 2015 and t.end == 2020

    def test_invalid_range(self):
        with pytest.raises(ValueError, match="start.*end"):
            TimeGroup(start=2020, end=2015)

    def test_out_of_bounds(self):
        with pytest.raises(ValueError, match="Year out of range"):
            TimeGroup(start=1800, end=2020)

class TestSpatialFilter:
    def test_valid_climate_zone(self):
        sf = SpatialFilter(type="climate_zone", value="tropical")
        assert sf.type == "climate_zone"

    def test_invalid_type(self):
        with pytest.raises(ValueError, match="Invalid spatial type"):
            SpatialFilter(type="invalid_type")

class TestAnalysisPlan:
    def test_minimal(self):
        plan = AnalysisPlan(intents=["kpi"], source="rule")
        assert plan.intents == ["kpi"]
        assert plan.granularity == "year"

    def test_invalid_intent(self):
        with pytest.raises(ValueError, match="Invalid intent"):
            AnalysisPlan(intents=["invalid_intent"])

    def test_invalid_granularity(self):
        with pytest.raises(ValueError, match="Invalid granularity"):
            AnalysisPlan(intents=["kpi"], granularity="hour")

    def test_invalid_metric(self):
        with pytest.raises(ValueError, match="Invalid metric"):
            AnalysisPlan(intents=["kpi"], metrics=["fake_metric"])

    def test_invalid_statistic(self):
        with pytest.raises(ValueError, match="Invalid statistic"):
            AnalysisPlan(intents=["trend_analysis"], statistics=["invalid_stat"])

    def test_dict_time_groups_conversion(self):
        plan = AnalysisPlan(intents=["kpi"], time_groups=[{"start":2015,"end":2020,"label":"test"}])
        assert isinstance(plan.time_groups[0], TimeGroup)
        assert plan.time_groups[0].start == 2015

    def test_dict_spatial_filter_conversion(self):
        plan = AnalysisPlan(intents=["kpi"], spatial_filter={"type":"climate_zone","value":"tropical"})
        assert isinstance(plan.spatial_filter, SpatialFilter)
        assert plan.spatial_filter.type == "climate_zone"

    def test_from_legacy_kpi(self):
        plan = AnalysisPlan.from_legacy_intent({"intent":"kpi","year":2024})
        assert plan.intents == ["kpi"]
        assert plan.time_groups[0].start == 2024

    def test_from_legacy_trend(self):
        plan = AnalysisPlan.from_legacy_intent({"intent":"trend_analysis","years":[2015,2025]})
        assert plan.intents == ["trend_analysis"]
        assert plan.statistics == ["linear_regression"]

    def test_from_legacy_ranking(self):
        plan = AnalysisPlan.from_legacy_intent({"intent":"ranking","category":"hottest","year":2024})
        assert plan.metrics == ["max_temperature"]

    def test_season_validation(self):
        with pytest.raises(ValueError, match="Invalid month"):
            AnalysisPlan(intents=["seasonal"], season=[13])

    def test_validate_plan_success(self):
        plan, errors = validate_plan({"intents":["kpi"]})
        assert plan is not None
        assert errors == []

    def test_validate_plan_failure(self):
        plan, errors = validate_plan({"intents":["bad_intent"]})
        assert plan is None
        assert len(errors) > 0
