"""AnalysisPlan Schema — 后端唯一允许跨模块传递的分析请求结构

手册 Section 4.1 要求：使用 Pydantic 定义并强制校验，LLM 只能输出受 JSON Schema 约束的 AnalysisPlan。
"""
from typing import Optional, Literal, Any
from dataclasses import dataclass, field, asdict
import json

# ── 枚举常量（统一维护，手册 4.2.2 要求） ──
VALID_INTENTS = ["kpi","monthly","ranking","zones","compare","trend_analysis",
                 "seasonal","zone_detail","extremes","station_query","page_analysis",
                 "trend","anomaly","distribution","summary"]
VALID_GRANULARITIES = ["day","month","year"]
VALID_SEASONS = {
    "spring": [3,4,5], "summer": [6,7,8],
    "autumn": [9,10,11], "winter": [12,1,2]
}
VALID_METRICS = ["avg_temperature","max_temperature","min_temperature",
                 "total_precip","extreme_days","heat_wave_days","cold_wave_days",
                 "frost_days","snow_days","thunder_days","obs_days","wind_speed"]
VALID_AGGREGATIONS = ["mean","sum","min","max","count","std","p5","p95"]
VALID_STATISTICS = ["linear_regression","mann_kendall","zscore_2sigma",
                    "sliding_average","t_test","anova","seasonal_decompose"]
VALID_SPATIAL_TYPES = ["region","station","climate_zone","bbox","country","all"]
VALID_CHART_GOALS = ["trend","compare","distribution","proportion","correlation","map","table"]


@dataclass
class TimeGroup:
    """一个时间段定义"""
    start: int
    end: int
    label: str = ""

    def __post_init__(self):
        if self.start > self.end:
            raise ValueError(f"start({self.start}) must be <= end({self.end})")
        if self.start < 1900 or self.end > 2100:
            raise ValueError(f"Year out of range: {self.start}-{self.end}")

@dataclass
class SpatialFilter:
    """空间过滤"""
    type: str  # region|station|climate_zone|bbox|country|all
    value: Any = None  # station ID, zone name, [lat_min,lat_max,lon_min,lon_max], etc.

    def __post_init__(self):
        if self.type not in VALID_SPATIAL_TYPES:
            raise ValueError(f"Invalid spatial type: {self.type} (allowed: {VALID_SPATIAL_TYPES})")

@dataclass
class AnalysisPlan:
    """结构化分析计划 — 手册 4.1 定义的核心契约"""
    # 意图（可多个）
    intents: list[str] = field(default_factory=lambda: ["summary"])

    # 时间段
    time_groups: list[TimeGroup] = field(default_factory=list)
    granularity: str = "year"  # day|month|year

    # 季节过滤（月份列表，空=全年）
    season: list[int] = field(default_factory=list)

    # 空间
    spatial_filter: SpatialFilter = field(default_factory=lambda: SpatialFilter(type="all"))

    # 指标与聚合
    metrics: list[str] = field(default_factory=lambda: ["avg_temperature"])
    aggregation: str = "mean"  # mean|sum|min|max|count|std|p5|p95
    group_by: list[str] = field(default_factory=list)  # year|month|climate_zone|station

    # 统计方法
    statistics: list[str] = field(default_factory=list)

    # 图表
    chart_goal: str = "trend"

    # 上下文
    page: str = ""           # 当前前端页面
    confidence: float = 0.0  # LLM 置信度

    # 元数据
    source: str = "rule"     # rule|llm|hybrid
    raw_question: str = ""

    def __post_init__(self):
        # 将 dict 格式的 time_groups 转为 TimeGroup 对象
        if self.time_groups:
            self.time_groups = [TimeGroup(**t) if isinstance(t, dict) else t for t in self.time_groups]
        if isinstance(self.spatial_filter, dict):
            self.spatial_filter = SpatialFilter(**self.spatial_filter)

        for i in self.intents:
            if i not in VALID_INTENTS:
                raise ValueError(f"Invalid intent: {i}")

        # 校验 granularity
        if self.granularity not in VALID_GRANULARITIES:
            raise ValueError(f"Invalid granularity: {self.granularity}")

        # 校验 metrics
        for m in self.metrics:
            if m not in VALID_METRICS:
                raise ValueError(f"Invalid metric: {m}")

        # 校验 aggregation
        if self.aggregation not in VALID_AGGREGATIONS:
            raise ValueError(f"Invalid aggregation: {self.aggregation}")

        # 校验 statistics
        for s in self.statistics:
            if s not in VALID_STATISTICS:
                raise ValueError(f"Invalid statistic: {s}")

        # 校验 chart_goal
        if self.chart_goal not in VALID_CHART_GOALS:
            raise ValueError(f"Invalid chart_goal: {self.chart_goal}")

        # 校验 season
        for m in self.season:
            if m < 1 or m > 12:
                raise ValueError(f"Invalid month in season: {m}")

    def to_dict(self) -> dict:
        d = asdict(self)
        d["time_groups"] = [asdict(t) for t in self.time_groups]
        return d

    @classmethod
    def from_legacy_intent(cls, intent_info: dict) -> "AnalysisPlan":
        """从旧意图格式转换（兼容旧 /agent/query）"""
        intent = intent_info.get("intent", "unknown")
        year = intent_info.get("year", 2025)
        years = intent_info.get("years", [year])

        if intent in ("kpi", "monthly", "zones"):
            return cls(
                intents=[intent],
                time_groups=[TimeGroup(start=year, end=year, label=str(year))],
                granularity="month" if intent == "monthly" else "year",
                metrics=["avg_temperature"] if intent != "zones" else ["avg_temperature"],
                chart_goal="trend" if intent == "monthly" else ("proportion" if intent == "zones" else "table"),
                source="rule"
            )

        if intent == "ranking":
            cat = intent_info.get("category", "hottest")
            metric_map = {"hottest":"max_temperature","coldest":"min_temperature",
                          "rainiest":"total_precip","most_extreme":"extreme_days"}
            return cls(
                intents=["ranking"],
                time_groups=[TimeGroup(start=year, end=year, label=str(year))],
                metrics=[metric_map.get(cat, "avg_temperature")],
                aggregation="max" if cat == "hottest" else "min" if cat == "coldest" else "sum",
                group_by=["station"],
                chart_goal="compare",
                source="rule"
            )

        if intent == "trend_analysis":
            return cls(
                intents=["trend_analysis"],
                time_groups=[TimeGroup(start=years[0], end=years[-1], label=f"{years[0]}-{years[-1]}")],
                granularity="month",
                metrics=["avg_temperature"],
                statistics=["linear_regression"],
                chart_goal="trend",
                source="rule"
            )

        if intent == "seasonal":
            return cls(
                intents=["seasonal"],
                time_groups=[TimeGroup(start=years[0], end=years[-1], label=f"{years[0]}-{years[-1]}")],
                granularity="month",
                season=list(range(1,13)),
                metrics=["avg_temperature"],
                chart_goal="compare",
                source="rule"
            )

        if intent == "compare":
            return cls(
                intents=["compare"],
                time_groups=[TimeGroup(start=y, end=y, label=str(y)) for y in years],
                metrics=["avg_temperature"],
                chart_goal="compare",
                source="rule"
            )

        # default
        return cls(
            intents=[intent],
            time_groups=[TimeGroup(start=year, end=year, label=str(year))],
            source="rule"
        )


def validate_plan(plan_dict: dict) -> tuple[AnalysisPlan | None, list[str]]:
    """校验并返回 AnalysisPlan + 错误列表"""
    errors = []
    try:
        plan = AnalysisPlan(**plan_dict)
        return plan, []
    except Exception as e:
        errors.append(str(e))
        return None, errors
