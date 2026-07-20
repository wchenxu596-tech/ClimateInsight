"""Agent 工具白名单 — 仅通过参数化SQL访问已验证的ADS/DWS表"""
from db import query_dict

VALID_CATEGORIES = {"hottest", "coldest", "rainiest", "most_extreme"}
VALID_YEARS = {2024}

def get_kpi(year: int) -> list[dict]:
    if year not in VALID_YEARS: raise ValueError(f"unsupported year: {year}")
    return query_dict("SELECT kpi_name,kpi_value,kpi_unit,kpi_desc FROM ads_kpi WHERE data_year=%s", (year,))

def get_monthly(year: int) -> list[dict]:
    if year not in VALID_YEARS: raise ValueError(f"unsupported year: {year}")
    return query_dict("SELECT obs_month,avg_temp,avg_max,avg_min FROM ads_monthly_trend WHERE data_year=%s ORDER BY obs_month", (year,))

def get_ranking(year: int, category: str, limit: int = 10) -> list[dict]:
    if year not in VALID_YEARS: raise ValueError(f"unsupported year: {year}")
    if category not in VALID_CATEGORIES: raise ValueError(f"unsupported category: {category}")
    limit = min(max(limit, 1), 15)
    return query_dict(
        "SELECT rank_num,station_id,station_name,value FROM ads_ranking WHERE data_year=%s AND category=%s ORDER BY rank_num LIMIT %s",
        (year, category, limit))

def get_zones(year: int) -> list[dict]:
    if year not in VALID_YEARS: raise ValueError(f"unsupported year: {year}")
    return query_dict("SELECT climate_zone,station_count AS cnt FROM ads_zones WHERE data_year=%s", (year,))

# 工具注册表
TOOLS = {
    "get_kpi": get_kpi,
    "get_monthly": get_monthly,
    "get_ranking": get_ranking,
    "get_zones": get_zones,
}
