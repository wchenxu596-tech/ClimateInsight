"""
ClimateInsight ETL Pipeline v2 — 流式聚合 + 年份主键 + 环境变量配置
用法: MYSQL_PASSWORD=xxx python scripts/etl_to_mysql.py [--year 2024]
"""
import subprocess, csv, io, os, sys, argparse
from collections import defaultdict
import pymysql

# ── 配置(环境变量) ──
DB = {
    "host": os.getenv("MYSQL_HOST", "127.0.0.1"),
    "port": int(os.getenv("MYSQL_PORT", "3306")),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.environ["MYSQL_PASSWORD"],
    "database": os.getenv("MYSQL_DATABASE", "climate_dw"),
    "charset": "utf8mb4",
}
HIVE_CONTAINER = os.getenv("HIVE_CONTAINER", "tier4_stu_hiveserver2")
HIVE_JDBC = os.getenv("HIVE_JDBC_URL", "jdbc:hive2://localhost:10000")
TARGET_YEAR = 2024

# ── Beeline 查询 ──
def beeline_tsv(sql):
    cmd = ["docker","exec","-i", HIVE_CONTAINER, "beeline",
           "-u", HIVE_JDBC, "-n","root","--silent=true","--outputformat=tsv2",
           "-e", f"USE climate_dw; {sql}"]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    lines = []
    for l in r.stdout.split("\n"):
        l = l.strip()
        if not l or "SLF4J" in l or "Picked" in l: continue
        if "jdbc:hive2" in l and ">" in l:
            l = l.split(">", 1)[-1].strip()
        lines.append(l)
    return "\n".join(lines)

# ── DWD → DWS 流式聚合 ──
def compute_dws(year):
    print(f"[DWS] 读取 DWD (year={year})...")
    csv_data = beeline_tsv(f"""
        SELECT station_id, station_name, obs_month,
               temp_mean, temp_max, temp_min, precip,
               is_rainy, is_extreme, is_heat_wave, is_cold_wave,
               has_frost, has_snow, has_thunder, latitude, longitude
        FROM dwd_climate_daily
        WHERE year={year} AND quality='valid'
          AND temp_max < 60 AND temp_min > -90 AND precip < 2000
    """)
    reader = csv.DictReader(io.StringIO(csv_data), delimiter="\t")
    
    agg = defaultdict(lambda: {"name":"","temps":[],"tmax":[],"tmin":[],
        "maxt":-999,"mint":999,"precip":0,"rain":0,"ext":0,"heat":0,"cold":0,
        "frost":0,"snow":0,"thunder":0,"obs":0,"lat":0,"lon":0})
    rejects = 0; total = 0
    
    for r in reader:
        total += 1
        sid = r.get("station_id","")
        mon = int(r.get("obs_month",0))
        key = (sid, year, mon)
        a = agg[key]
        a["name"] = r.get("station_name","")
        try:
            t = float(r["temp_mean"]); a["temps"].append(t)
            tm = float(r["temp_max"]); a["tmax"].append(tm); a["maxt"] = max(a["maxt"], tm)
            tn = float(r["temp_min"]); a["tmin"].append(tn); a["mint"] = min(a["mint"], tn)
        except: rejects += 1; continue
        try: a["precip"] += float(r["precip"])
        except: pass
        a["rain"] += int(r.get("is_rainy",0))
        a["ext"] += int(r.get("is_extreme",0))
        a["heat"] += int(r.get("is_heat_wave",0))
        a["cold"] += int(r.get("is_cold_wave",0))
        a["frost"] += int(r.get("has_frost",0))
        a["snow"] += int(r.get("has_snow",0))
        a["thunder"] += int(r.get("has_thunder",0))
        a["obs"] += 1
        try: a["lat"] = float(r["latitude"]); a["lon"] = float(r["longitude"])
        except: pass
    
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
        avg_t = sum(a["temps"])/len(a["temps"]) if a["temps"] else 0
        avg_tmax = sum(a["tmax"])/len(a["tmax"]) if a["tmax"] else 0
        avg_tmin = sum(a["tmin"])/len(a["tmin"]) if a["tmin"] else 0
        
        # 气候带
        if abs(a["lat"]) >= 60 or avg_t < 0: zone = "polar"
        elif avg_t >= 18 and a["mint"] >= 18: zone = "tropical"
        elif avg_t >= 10: zone = "temperate"
        elif a["precip"]/max(a["obs"],1) < 10: zone = "arid"
        else: zone = "continental"
        
        batch.append((sid, a["name"][:200], yr, mon, round(a["lat"],4), round(a["lon"],4),
            round(avg_t,1), round(avg_tmax,1), round(avg_tmin,1),
            round(a["maxt"],1), round(a["mint"],1), round(a["precip"],1),
            a["rain"], a["ext"], a["heat"], a["cold"],
            a["frost"], a["snow"], a["thunder"], a["obs"], zone))
        if len(batch) >= 500:
            cur.executemany(sql, batch); batch = []
    if batch: cur.executemany(sql, batch)
    conn.commit(); conn.close()
    print(f"[DWS] 写入 {len(agg)} 条")

# ── ADS 计算 ──
def compute_ads(year):
    conn = pymysql.connect(**DB)
    cur = conn.cursor()
    
    # KPI
    cur.execute("""SELECT AVG(avg_temp), COUNT(DISTINCT station_id),
        SUM(extreme_days)*100.0/SUM(obs_days), MAX(max_temp)
        FROM dws_station_monthly WHERE year=%s""", (year,))
    avg_t, stns, ext_pct, htemp = cur.fetchone()
    cur.execute("DELETE FROM ads_kpi WHERE data_year=%s", (year,))
    cur.executemany("INSERT INTO ads_kpi VALUES(%s,%s,%s,%s,%s)", [
        ("global_avg_temp", round(float(avg_t or 0),2), "°C", "全球年平均温度", year),
        ("total_stations", int(stns or 0), "个", "活跃气象站总数", year),
        ("extreme_event_pct", round(float(ext_pct or 0),2), "%", "极端天气日数占比", year),
        ("hottest_station_temp", round(float(htemp or 0),1), "°C", "年度最高气温", year),
    ])
    
    # 月度趋势
    cur.execute("DELETE FROM ads_monthly_trend WHERE data_year=%s", (year,))
    cur.execute("""INSERT INTO ads_monthly_trend(data_year,obs_month,avg_temp,avg_max,avg_min)
        SELECT %s,obs_month,AVG(avg_temp),AVG(avg_temp_max),AVG(avg_temp_min)
        FROM dws_station_monthly WHERE year=%s GROUP BY obs_month""", (year,year))
    
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
    
    conn.commit(); conn.close()
    print(f"[ADS] KPI+趋势+排名+气候带 写入完成 (year={year})")

# ── 主流程 ──
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, default=TARGET_YEAR)
    args = parser.parse_args()
    print(f"ClimateInsight ETL — year={args.year}")
    compute_dws(args.year)
    compute_ads(args.year)
    print("✅ ETL完成")
