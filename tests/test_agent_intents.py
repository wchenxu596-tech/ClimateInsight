"""意图识别单元测试"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from agent.intents import detect


class TestIntentDetection:
    """意图识别: KPI、月度、四类排名、气候带、帮助、未知 """

    def test_kpi_intent(self):
        cases = [
            "2024年全球平均气温？",
            "年均温是多少",
            "kpi指标",
            "全球平均气温",
        ]
        for q in cases:
            r = detect(q)
            assert r["intent"] == "kpi", f"'{q}' → 期望 kpi, 实际 {r['intent']}"

    def test_monthly_intent(self):
        cases = [
            "各月温度变化？",
            "月度趋势",
            "每月气温",
            "12个月的月均温度",
        ]
        for q in cases:
            r = detect(q)
            assert r["intent"] == "monthly", f"'{q}' → 期望 monthly, 实际 {r['intent']}"

    def test_ranking_hottest(self):
        r = detect("最热的10个站点")
        assert r["intent"] == "ranking"
        assert r["category"] == "hottest"
        assert r["limit"] == 10

    def test_ranking_coldest(self):
        r = detect("最冷的5个站点")
        assert r["intent"] == "ranking"
        assert r["category"] == "coldest"
        assert r["limit"] == 5

    def test_ranking_rainiest(self):
        r = detect("降水最多的站点")
        assert r["intent"] == "ranking"
        assert r["category"] == "rainiest"

    def test_ranking_extreme(self):
        r = detect("极端天气最多的15个站")
        assert r["intent"] == "ranking"
        assert r["category"] == "most_extreme"
        assert r["limit"] == 15

    def test_zones_intent(self):
        r = detect("气候带分布")
        assert r["intent"] == "zones"

    def test_help_intent(self):
        for q in ["帮助", "能做什么", "怎么用", "功能"]:
            r = detect(q)
            assert r["intent"] == "help", f"'{q}' → 期望 help, 实际 {r['intent']}"

    def test_unknown_intent(self):
        for q in ["今天天气怎么样", "what is the weather", "随机文本xyz"]:
            r = detect(q)
            assert r["intent"] == "unknown", f"'{q}' → 期望 unknown, 实际 {r['intent']}"

    def test_limit_cap(self):
        """limit 上限为15"""
        r = detect("前50个最热的站")
        assert r["limit"] == 15

    def test_year_extraction(self):
        r = detect("2024年最热的站？")
        assert r["year"] == 2024
