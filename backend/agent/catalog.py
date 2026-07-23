"""DatasetCatalog — 可查询数据集、字段映射、聚合白名单

手册 Section 4.3 要求：
- query_builder 只接收已验证的 QuerySpec
- SQL 表名和列名仅能从 Catalog 选择
- 值一律作为数据库参数绑定
"""
from typing import Optional

# ── 数据集定义 ──
DATASETS = {
    "dws_monthly": {
        "table": "dws_station_monthly",
        "description": "站×月聚合 (DWS)",
        "granularity": "month",
        "year_range": (2015, 2025),
        "max_rows_per_query": 50000,
        "columns": {
            "station_id":    {"type": "string", "filterable": True,  "groupable": True},
            "station_name":  {"type": "string", "filterable": False, "groupable": False},
            "year":          {"type": "int",    "filterable": True,  "groupable": True},
            "obs_month":     {"type": "int",    "filterable": True,  "groupable": True},
            "latitude":      {"type": "float",  "filterable": True,  "groupable": False},
            "longitude":     {"type": "float",  "filterable": True,  "groupable": False},
            "avg_temp":      {"type": "float",  "filterable": False, "groupable": False},
            "avg_temp_max":  {"type": "float",  "filterable": False, "groupable": False},
            "avg_temp_min":  {"type": "float",  "filterable": False, "groupable": False},
            "max_temp":      {"type": "float",  "filterable": False, "groupable": False},
            "min_temp":      {"type": "float",  "filterable": False, "groupable": False},
            "total_precip":  {"type": "float",  "filterable": False, "groupable": False},
            "extreme_days":  {"type": "int",    "filterable": False, "groupable": False},
            "heat_wave_days":{"type": "int",    "filterable": False, "groupable": False},
            "cold_wave_days":{"type": "int",    "filterable": False, "groupable": False},
            "frost_days":    {"type": "int",    "filterable": False, "groupable": False},
            "snow_days":     {"type": "int",    "filterable": False, "groupable": False},
            "thunder_days":  {"type": "int",    "filterable": False, "groupable": False},
            "obs_days":      {"type": "int",    "filterable": False, "groupable": False},
            "climate_zone":  {"type": "string", "filterable": True,  "groupable": True},
            "rainy_days":    {"type": "int",    "filterable": False, "groupable": False},
        }
    },
    "ads_kpi": {
        "table": "ads_kpi",
        "description": "年度KPI (ADS)",
        "granularity": "year",
        "year_range": (2015, 2025),
        "max_rows_per_query": 100,
        "columns": {
            "data_year":   {"type": "int",    "filterable": True,  "groupable": True},
            "kpi_name":    {"type": "string", "filterable": True,  "groupable": True},
            "kpi_value":   {"type": "float",  "filterable": False, "groupable": False},
            "kpi_unit":    {"type": "string", "filterable": False, "groupable": False},
            "kpi_desc":    {"type": "string", "filterable": False, "groupable": False},
        }
    },
    "ads_monthly_trend": {
        "table": "ads_monthly_trend",
        "description": "月度趋势 (ADS)",
        "granularity": "month",
        "year_range": (2015, 2025),
        "max_rows_per_query": 200,
        "columns": {
            "data_year": {"type": "int",   "filterable": True,  "groupable": True},
            "obs_month": {"type": "int",   "filterable": True,  "groupable": True},
            "avg_temp":  {"type": "float", "filterable": False, "groupable": False},
            "avg_max":   {"type": "float", "filterable": False, "groupable": False},
            "avg_min":   {"type": "float", "filterable": False, "groupable": False},
        }
    },
    "ads_stations": {
        "table": "ads_stations",
        "description": "站点概要 (ADS, 预聚合)",
        "granularity": "year",
        "year_range": (2015, 2025),
        "max_rows_per_query": 20000,
        "columns": {
            "data_year":    {"type": "int",    "filterable": True,  "groupable": True},
            "station_id":   {"type": "string", "filterable": True,  "groupable": True},
            "station_name": {"type": "string", "filterable": False, "groupable": False},
            "lat":          {"type": "float",  "filterable": True,  "groupable": False},
            "lon":          {"type": "float",  "filterable": True,  "groupable": False},
            "climate_zone": {"type": "string", "filterable": True,  "groupable": True},
            "avg_temp":     {"type": "float",  "filterable": False, "groupable": False},
            "total_precip": {"type": "float",  "filterable": False, "groupable": False},
            "risk_events":  {"type": "int",    "filterable": False, "groupable": False},
        }
    },
    "ads_zone_trends": {
        "table": "ads_zone_trends",
        "description": "气候带趋势 (ADS, 预聚合)",
        "granularity": "year",
        "year_range": (2015, 2025),
        "max_rows_per_query": 100,
        "columns": {
            "data_year":     {"type": "int",    "filterable": True,  "groupable": True},
            "climate_zone":  {"type": "string", "filterable": True,  "groupable": True},
            "avg_temp":      {"type": "float",  "filterable": False, "groupable": False},
            "avg_precip":    {"type": "float",  "filterable": False, "groupable": False},
            "extreme_days":  {"type": "int",    "filterable": False, "groupable": False},
            "heat_wave_days":{"type": "int",    "filterable": False, "groupable": False},
            "cold_wave_days":{"type": "int",    "filterable": False, "groupable": False},
            "station_count": {"type": "int",    "filterable": False, "groupable": False},
        }
    },
}

# ── 要素名称 → 表+列映射 ──
METRIC_TO_COLUMN = {
    "avg_temperature":  {"dataset": "ads_monthly_trend", "column": "avg_temp",  "unit": "°C"},
    "max_temperature":  {"dataset": "ads_monthly_trend", "column": "avg_max",   "unit": "°C"},
    "min_temperature":  {"dataset": "ads_monthly_trend", "column": "avg_min",   "unit": "°C"},
    "total_precip":     {"dataset": "ads_stations",      "column": "total_precip","unit":"mm"},
    "extreme_days":     {"dataset": "ads_zone_trends",   "column": "extreme_days", "unit":"天"},
    "heat_wave_days":   {"dataset": "ads_zone_trends",   "column": "heat_wave_days","unit":"天"},
    "cold_wave_days":   {"dataset": "ads_zone_trends",   "column": "cold_wave_days","unit":"天"},
}

# ── 聚合函数白名单 ──
ALLOWED_AGG_FUNCTIONS = {
    "mean": "AVG",
    "sum":  "SUM",
    "min":  "MIN",
    "max":  "MAX",
    "count":"COUNT",
    "std":  "STDDEV",
}

# ── 空间过滤白名单 ──
CLIMATE_ZONES = {"tropical","temperate","arid","continental","polar"}

# 大洲经纬度绑定（用于 bbox 查询）
CONTINENT_BBOX = {
    "亚洲":   (0, 80, 26, 180),
    "非洲":   (-35, 38, -18, 52),
    "欧洲":   (35, 72, -25, 40),
    "北美洲": (15, 75, -170, -50),
    "南美洲": (-56, 12, -82, -34),
    "大洋洲": (-50, 0, 110, 180),
    "南极洲": (-90, -60, -180, 180),
}


def validate_table_column(dataset_name: str, column_name: str) -> bool:
    """校验表名和列名是否在白名单中"""
    ds = DATASETS.get(dataset_name)
    if not ds: return False
    return column_name in ds["columns"]

def validate_metric(metric: str) -> bool:
    return metric in METRIC_TO_COLUMN

def validate_spatial(spatial_type: str, value) -> bool:
    """校验空间过滤参数"""
    if spatial_type == "climate_zone":
        return value in CLIMATE_ZONES
    if spatial_type == "bbox":
        if not isinstance(value, (list, tuple)) or len(value) != 4:
            return False
        lat_min, lat_max, lon_min, lon_max = value
        return -90 <= lat_min <= lat_max <= 90 and -180 <= lon_min <= lon_max <= 180
    if spatial_type == "country":
        return isinstance(value, str) and len(value) > 0
    if spatial_type == "all":
        return True
    return True
