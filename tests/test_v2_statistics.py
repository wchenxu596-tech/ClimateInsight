"""Phase 7: 统计工具单元测试"""
import pytest, sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
from agent.statistics import linear_regression, zscore_anomaly, sliding_average, descriptive_stats

class TestLinearRegression:
    def test_basic_trend(self):
        r = linear_regression([2015,2016,2017,2018,2019],[12.8,13.1,13.2,13.1,13.2])
        assert r["method"] == "linear_regression"
        assert abs(r["slope"] - 0.08) < 0.05
        assert r["sample_count"] == 5

    def test_perfect_linear(self):
        r = linear_regression([1,2,3,4,5],[2,4,6,8,10])
        assert abs(r["r_squared"] - 1.0) < 0.001
        assert abs(r["slope"] - 2.0) < 0.001

    def test_insufficient_samples(self):
        r = linear_regression([1,2],[3,4])
        assert "error" in r
        assert "样本量不足" in r["error"]

    def test_with_none(self):
        r = linear_regression([1,2,3,4,5],[1.0,None,3.0,4.0,5.0])
        assert r["sample_count"] == 4  # None excluded

class TestZScoreAnomaly:
    def test_basic(self):
        data = [10,10,10,10, 50, 10,10,10,10]
        r = zscore_anomaly(data, threshold=2.0)
        assert r["anomaly_count"] == 1
        assert r["anomalies"][0]["index"] == 4

    def test_no_anomaly(self):
        r = zscore_anomaly([10,11,9,10,10,11,9,10], threshold=3.0)
        assert r["anomaly_count"] == 0

    def test_small_sample(self):
        r = zscore_anomaly([1,2], threshold=2.0)
        assert "error" in r

class TestSlidingAverage:
    def test_basic(self):
        r = sliding_average([1,3,5,7,9], window=3)
        assert r["smoothed"][0] == 1.0  # first element: window of 1
        assert r["smoothed"][4] == 7.0  # 5+7+9/3

    def test_small_window(self):
        r = sliding_average([1,2], window=1)
        assert "error" in r

class TestDescriptiveStats:
    def test_basic(self):
        r = descriptive_stats([1,2,3,4,5])
        assert r["mean"] == 3.0
        assert r["min"] == 1
        assert r["max"] == 5
        assert r["median"] == 3

    def test_empty(self):
        r = descriptive_stats([])
        assert "error" in r
