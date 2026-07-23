"""Agent 工具白名单 — 仅通过参数化SQL访问已验证的ADS/DWS表"""
from db import query_dict

VALID_CATEGORIES = {"hottest", "coldest", "rainiest", "most_extreme"}
VALID_YEARS = {2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025}

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

# ── 新增工具 ──

def get_kpi_history(years: list[int]) -> dict[int, list[dict]]:
    """多年KPI数据"""
    valid = [y for y in years if y in VALID_YEARS]
    if not valid: raise ValueError("no valid years")
    rows = query_dict(
        "SELECT data_year as year,kpi_name,kpi_value,kpi_unit FROM ads_kpi WHERE data_year IN ({}) ORDER BY data_year,kpi_name"
        .format(",".join(["%s"] * len(valid))), tuple(valid))
    result = {}
    for y in valid: result[y] = [r for r in rows if r["year"] == y]
    return result

def get_trend_multi_year(years: list[int]) -> dict[int, list[dict]]:
    """多年月度温度趋势"""
    valid = [y for y in years if y in VALID_YEARS]
    if not valid: raise ValueError("no valid years")
    rows = query_dict(
        "SELECT data_year as year,obs_month as month,avg_temp,avg_max,avg_min FROM ads_monthly_trend WHERE data_year IN ({}) ORDER BY data_year,obs_month"
        .format(",".join(["%s"] * len(valid))), tuple(valid))
    result = {}
    for y in valid: result[y] = [r for r in rows if r["year"] == y]
    return result

def get_zones_trend(years: list[int]) -> dict[int, list[dict]]:
    """多年气候带趋势（温度/降水/极端）— 使用ADS表极速查询"""
    valid = [y for y in years if y in VALID_YEARS]
    if not valid: raise ValueError("no valid years")
    rows = query_dict(
        "SELECT data_year as year,climate_zone,avg_temp,avg_precip,"
        "extreme_days,heat_wave_days,cold_wave_days,station_count "
        "FROM ads_zone_trends WHERE data_year IN ({}) ORDER BY data_year,climate_zone"
        .format(",".join(["%s"] * len(valid))), tuple(valid))
    result = {}
    for y in valid: result[y] = [r for r in rows if r["year"] == y]
    return result

def get_station_detail(station_id: str, year: int) -> dict:
    """单站月度明细"""
    if year not in VALID_YEARS: raise ValueError(f"unsupported year: {year}")
    info = query_dict(
        "SELECT station_id,station_name,ROUND(latitude,4) as lat,ROUND(longitude,4) as lon,climate_zone "
        "FROM dws_station_monthly WHERE station_id=%s AND year=%s LIMIT 1", (station_id, year))
    months = query_dict(
        "SELECT obs_month,ROUND(avg_temp,1) as avg_temp,ROUND(avg_temp_max,1) as avg_max,"
        "ROUND(avg_temp_min,1) as avg_min,ROUND(total_precip,1) as precip,"
        "rainy_days,extreme_days,heat_wave_days,cold_wave_days,frost_days,snow_days,thunder_days,obs_days "
        "FROM dws_station_monthly WHERE station_id=%s AND year=%s ORDER BY obs_month", (station_id, year))
    return {"info": info[0] if info else None, "months": months}

# 工具注册表
TOOLS = {
    "get_kpi": get_kpi,
    "get_monthly": get_monthly,
    "get_ranking": get_ranking,
    "get_zones": get_zones,
    "get_kpi_history": get_kpi_history,
    "get_trend_multi_year": get_trend_multi_year,
    "get_zones_trend": get_zones_trend,
    "get_station_detail": get_station_detail,
}
