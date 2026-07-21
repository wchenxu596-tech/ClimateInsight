"""
ClimateInsight CSV→MySQL ETL — 从预处理CSV直接写入MySQL DWS/ADS
用法: MYSQL_PASSWORD=xxx python scripts/etl_csv_to_mysql.py --year 2022 --csv data/climate_2022.csv

适用于Hive/YARN不可用时，复刻 etl_to_mysql.py 的聚合逻辑
"""
import csv, os, sys, argparse
from collections import defaultdict
import pymysql

# ── 配置 ──
DB = {
    "host": os.getenv("MYSQL_HOST", "127.0.0.1"),
    "port": int(os.getenv("MYSQL_PORT", "3306")),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.environ["MYSQL_PASSWORD"],
    "database": os.getenv("MYSQL_DATABASE", "climate_dw"),
    "charset": "utf8mb4",
}


def compute_dws(csv_path: str, year: int):
    """从预处理CSV聚合DWS (复刻 etl_to_mysql.py 的逻辑)"""
    print(f"[DWS] 读取 {csv_path} (year={year})...")

    agg = defaultdict(lambda: {
        "name": "", "temps": [], "tmax": [], "tmin": [],
        "maxt": -999, "mint": 999, "precip": 0, "rain": 0, "ext": 0,
        "heat": 0, "cold": 0, "frost": 0, "snow": 0, "thunder": 0,
        "obs": 0, "lat": 0, "lon": 0
    })
    rejects = total = 0

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            total += 1
            sid = r.get("station_id", "")
            mon = int(r.get("month", 0))
            key = (sid, year, mon)
            a = agg[key]
            a["name"] = r.get("station_name", "")

            try:
                t = float(r.get("temp_mean_c", 0))
                tm = float(r.get("temp_max_c", 0))
                tn = float(r.get("temp_min_c", 0))
            except (ValueError, TypeError):
                rejects += 1
                continue

            # 温度范围过滤
            if tm >= 60 or tn <= -90:
                rejects += 1
                continue

            a["temps"].append(t)
            a["tmax"].append(tm)
            a["tmin"].append(tn)
            a["maxt"] = max(a["maxt"], tm)
            a["mint"] = min(a["mint"], tn)

            try:
                precip = float(r.get("precip_mm", 0))
            except (ValueError, TypeError):
                precip = 0

            if precip >= 2000:  # 异常降水跳过
                rejects += 1
                continue

            a["precip"] += precip
            a["rain"] += 1 if precip > 0 else 0

            # 极端/热浪/寒潮
            is_heat = 1 if tm >= 35 else 0
            is_cold = 1 if tn <= -10 else 0
            is_ext = 1 if (tm >= 35 or tn <= -10 or precip >= 25) else 0
            a["heat"] += is_heat
            a["cold"] += is_cold
            a["ext"] += is_ext

            # 天气标志
            a["frost"] += int(r.get("has_frost", 0) or 0)
            a["snow"] += int(r.get("has_snow", 0) or 0)
            a["thunder"] += int(r.get("has_thunder", 0) or 0)
            a["obs"] += 1

            try:
                a["lat"] = float(r["latitude"])
                a["lon"] = float(r["longitude"])
            except (ValueError, TypeError):
                pass

    print(f"[DWS] {total} 行 → {len(agg)} 聚合组, 拒绝 {rejects} 行")

    conn = pymysql.connect(**DB)
    cur = conn.cursor()
    cur.execute("DELETE FROM dws_station_monthly WHERE year=%s", (year,))

    sql = """INSERT INTO dws_station_monthly
        (station_id,station_name,year,obs_month,latitude,longitude,
         avg_temp,avg_temp_max,avg_temp_min,max_temp,min_temp,
         total_precip,rainy_days,extreme_days,heat_wave_days,cold_wave_days,
         frost_days,snow_days,thunder_days,obs_days,climate_zone)
        VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

    batch = []
    for (sid, yr, mon), a in agg.items():
        n = len(a["temps"])
        if n == 0:
            continue
        avg_t = sum(a["temps"]) / n
        avg_tmax = sum(a["tmax"]) / n
        avg_tmin = sum(a["tmin"]) / n

        # 气候带
        lat = a["lat"]
        if abs(lat) >= 60 or avg_t < 0:
            zone = "polar"
        elif avg_t >= 18 and a["mint"] >= 18:
            zone = "tropical"
        elif avg_t >= 10:
            zone = "temperate"
        elif a["precip"] / max(a["obs"], 1) < 10:
            zone = "arid"
        else:
            zone = "continental"

        batch.append((sid, a["name"][:200], yr, mon, round(lat, 4), round(a["lon"], 4),
            round(avg_t, 1), round(avg_tmax, 1), round(avg_tmin, 1),
            round(a["maxt"], 1), round(a["mint"], 1), round(a["precip"], 1),
            a["rain"], a["ext"], a["heat"], a["cold"],
            a["frost"], a["snow"], a["thunder"], a["obs"], zone))

        if len(batch) >= 500:
            cur.executemany(sql, batch)
            batch = []
    if batch:
        cur.executemany(sql, batch)

    conn.commit()
    conn.close()
    print(f"[DWS] 写入 {len(agg)} 条")


def compute_ads(year: int):
    """从DWS计算ADS (同 etl_to_mysql.py)"""
    conn = pymysql.connect(**DB)
    cur = conn.cursor()

    # KPI
    cur.execute("""SELECT AVG(avg_temp), COUNT(DISTINCT station_id),
        SUM(extreme_days)*100.0/SUM(obs_days), MAX(max_temp)
        FROM dws_station_monthly WHERE year=%s""", (year,))
    avg_t, stns, ext_pct, htemp = cur.fetchone()
    cur.execute("DELETE FROM ads_kpi WHERE data_year=%s", (year,))
    cur.executemany("INSERT INTO ads_kpi VALUES(%s,%s,%s,%s,%s)", [
        ("global_avg_temp", round(float(avg_t or 0), 2), "°C", "全球年平均温度", year),
        ("total_stations", int(stns or 0), "个", "活跃气象站总数", year),
        ("extreme_event_pct", round(float(ext_pct or 0), 2), "%", "极端天气日数占比", year),
        ("hottest_station_temp", round(float(htemp or 0), 1), "°C", "年度最高气温", year),
    ])

    # 月度趋势
    cur.execute("DELETE FROM ads_monthly_trend WHERE data_year=%s", (year,))
    cur.execute("""INSERT INTO ads_monthly_trend(data_year,obs_month,avg_temp,avg_max,avg_min)
        SELECT %s,obs_month,AVG(avg_temp),AVG(avg_temp_max),AVG(avg_temp_min)
        FROM dws_station_monthly WHERE year=%s GROUP BY obs_month""", (year, year))

    # 排名
    cur.execute("DELETE FROM ads_ranking WHERE data_year=%s", (year,))
    rank_sqls = [
        ("hottest", "AVG(avg_temp_max) DESC"),
        ("coldest", "AVG(avg_temp_min) ASC"),
        ("rainiest", "SUM(total_precip) DESC"),
        ("most_extreme", "SUM(extreme_days) DESC"),
    ]
    for cat, order in rank_sqls:
        cur.execute(f"""SELECT station_id,station_name,ROUND({order.split()[0]},1)
            FROM dws_station_monthly WHERE year=%s GROUP BY 1,2 ORDER BY 3 {order.split()[1]} LIMIT 15""", (year,))
        for i, row in enumerate(cur.fetchall()):
            cur.execute("INSERT INTO ads_ranking(category,data_year,rank_num,station_id,station_name,value) VALUES(%s,%s,%s,%s,%s,%s)",
                (cat, year, i+1, row[0], row[1], float(row[2])))

    # 气候带
    cur.execute("DELETE FROM ads_zones WHERE data_year=%s", (year,))
    cur.execute("SELECT climate_zone, COUNT(DISTINCT station_id) FROM dws_station_monthly WHERE year=%s GROUP BY 1", (year,))
    for zone, cnt in cur.fetchall():
        cur.execute("INSERT INTO ads_zones VALUES(%s,%s,%s)", (zone, cnt, year))

    conn.commit()
    conn.close()
    print(f"[ADS] KPI+趋势+排名+气候带 写入完成 (year={year})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--csv", type=str, required=True)
    args = parser.parse_args()
    print(f"ClimateInsight CSV→MySQL ETL — year={args.year}")
    compute_dws(args.csv, args.year)
    compute_ads(args.year)
    print("✅ ETL完成")
