"""
ClimateInsight 一键数据加载
============================
从 NOAA GSOD 官网下载原始数据 → 预处理 → 写入 MySQL

用法:
  docker compose run --rm setup-data python /scripts/download_and_load.py --year 2024
  # 或本地: MYSQL_PASSWORD=xxx python scripts/download_and_load.py --year 2024
"""
import os, sys, json, csv, io, gzip, tarfile, argparse, urllib.request, textwrap
from collections import defaultdict
from datetime import datetime
from pathlib import Path

# ── 配置 ──
DATA_DIR = Path(os.getenv("DATA_DIR", "/data"))
RAW_DIR = DATA_DIR / "raw"
OUTPUT_DIR = DATA_DIR / "processed"

NOAA_URL = "https://www.ncei.noaa.gov/data/global-summary-of-the-day/archive/{year}.tar.gz"

DB_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "127.0.0.1"),
    "port": int(os.getenv("MYSQL_PORT", "3306")),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.environ.get("MYSQL_PASSWORD", ""),
    "database": os.getenv("MYSQL_DATABASE", "climate_dw"),
}

# ── 字段映射 ──
COL_MAP = {
    "STATION": "station_id", "DATE": "obs_date",
    "LATITUDE": "latitude", "LONGITUDE": "longitude",
    "ELEVATION": "elevation", "NAME": "station_name",
    "TEMP": "temp_mean_f", "DEWP": "dew_point_f",
    "SLP": "pressure_slp", "STP": "pressure_stp",
    "VISIB": "visibility", "WDSP": "wind_speed",
    "MXSPD": "wind_max_speed", "GUST": "wind_gust",
    "MAX": "temp_max_f", "MIN": "temp_min_f",
    "PRCP": "precip_inches", "SNDP": "snow_depth",
    "FRSHTT": "weather_flags",
}
KEEP_COLS = list(COL_MAP.keys())


# ═══════════════════════════════════════════
#  步骤 1: 下载 NOAA GSOD 年度归档
# ═══════════════════════════════════════════
def download_year(year: int) -> Path:
    url = NOAA_URL.format(year=year)
    dest = RAW_DIR / f"{year}.tar.gz"
    if dest.exists() and dest.stat().st_size > 1_000_000:
        print(f"[跳过] {dest} 已存在 ({dest.stat().st_size/1024/1024:.0f} MB)")
        return dest

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[下载] {url}")
    print(f"[目标] {dest}")
    print("[提示] NOAA GSOD 年度数据约 500MB，下载可能需要几分钟...")

    try:
        urllib.request.urlretrieve(url, dest)
        print(f"[完成] 下载完成 ({dest.stat().st_size/1024/1024:.0f} MB)")
        return dest
    except Exception as e:
        print(f"[错误] 下载失败: {e}")
        print("[建议] 手动下载后放到 data/raw/ 目录下")
        sys.exit(1)


# ═══════════════════════════════════════════
#  步骤 2: 提取并合并为单个 CSV
# ═══════════════════════════════════════════
def extract_and_merge(tar_path: Path, year: int) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_file = OUTPUT_DIR / f"climate_{year}.csv"
    if out_file.exists():
        print(f"[跳过] {out_file} 已存在")
        return out_file

    print(f"[提取] 解压 {tar_path.name} ...")

    # 输出表头
    header = list(COL_MAP.values()) + [
        "temp_mean_c", "temp_max_c", "temp_min_c", "precip_mm",
        "year", "month", "day",
        "has_frost", "has_rain", "has_snow",
        "has_hail", "has_thunder", "has_tornado",
        "quality_flag",
    ]

    total = 0
    with tarfile.open(tar_path, "r:gz") as tar, \
         open(out_file, "w", newline="", encoding="utf-8") as fout:

        writer = csv.writer(fout)
        writer.writerow(header)

        members = [m for m in tar.getmembers() if m.name.endswith(".csv")]
        print(f"[提取] {len(members)} 个气象站文件")

        for i, m in enumerate(members):
            if (i + 1) % 2000 == 0:
                print(f"  进度: {i+1}/{len(members)} ({total} 行)")

            f = tar.extractfile(m)
            if not f:
                continue

            for row in csv.DictReader(io.TextIOWrapper(f, encoding="utf-8")):
                row_year = row.get("DATE", "")[:4]
                if row_year != str(year):
                    continue

                # 清洗
                temp_f = _clean_float(row.get("TEMP"))
                temp_max_f = _clean_float(row.get("MAX"))
                temp_min_f = _clean_float(row.get("MIN"))
                precip_in = _clean_float(row.get("PRCP"))
                lat = _clean_float(row.get("LATITUDE"))
                lon = _clean_float(row.get("LONGITUDE"))

                # 跳过无效数据
                if temp_f is None or lat is None or lat == 0:
                    continue

                # 温度转换
                temp_c = _f_to_c(temp_f)
                temp_max_c = _f_to_c(temp_max_f) if temp_max_f is not None else None
                temp_min_c = _f_to_c(temp_min_f) if temp_min_f is not None else None
                precip_mm = _inch_to_mm(precip_in) if precip_in is not None else None

                # 日期
                try:
                    dt = datetime.strptime(row.get("DATE", ""), "%Y-%m-%d")
                except ValueError:
                    continue

                # 气象标记
                flags = _parse_flags(row.get("FRSHTT", "000000"))

                # 质量
                quality = "valid"
                if temp_c is not None and (temp_c < -90 or temp_c > 60):
                    quality = "suspicious"

                base = [
                    row.get("STATION", ""), row.get("DATE", ""),
                    lat, lon, _clean_float(row.get("ELEVATION")),
                    row.get("NAME", "").strip().replace('"', ''),
                    temp_f, _clean_float(row.get("DEWP")),
                    _clean_float(row.get("SLP")), _clean_float(row.get("STP")),
                    _clean_float(row.get("VISIB")), _clean_float(row.get("WDSP")),
                    _clean_float(row.get("MXSPD")), _clean_float(row.get("GUST")),
                    temp_max_f, temp_min_f, precip_in,
                    _clean_float(row.get("SNDP")), row.get("FRSHTT", ""),
                ]

                derived = [
                    temp_c, temp_max_c, temp_min_c, precip_mm,
                    dt.year, dt.month, dt.day,
                    flags["frost"], flags["rain"], flags["snow"],
                    flags["hail"], flags["thunder"], flags["tornado"],
                    quality,
                ]
                writer.writerow(base + derived)
                total += 1

    print(f"[完成] 合并完成: {total} 行 → {out_file}")
    return out_file


# ═══════════════════════════════════════════
#  步骤 3: 聚合 → MySQL
# ═══════════════════════════════════════════
def load_to_mysql(csv_path: Path, year: int):
    import pymysql

    print(f"[聚合] 读取 {csv_path} ...")
    agg = defaultdict(lambda: {
        "name": "", "temps": [], "tmax": [], "tmin": [],
        "maxt": -999, "mint": 999, "precip": 0, "rain": 0, "ext": 0,
        "heat": 0, "cold": 0, "frost": 0, "snow": 0, "thunder": 0,
        "obs": 0, "lat": 0, "lon": 0,
    })
    total = 0

    with open(csv_path, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sid = row.get("station_id", "")
            mon = int(row.get("month", 0))
            key = (sid, year, mon)
            a = agg[key]
            a["name"] = row.get("station_name", "")

            t = _safe_float(row.get("temp_mean_c"))
            tm = _safe_float(row.get("temp_max_c"))
            tn = _safe_float(row.get("temp_min_c"))
            pr = _safe_float(row.get("precip_mm"))
            if t is None:
                continue

            a["temps"].append(t)
            if tm is not None:
                a["tmax"].append(tm)
                a["maxt"] = max(a["maxt"], tm)
            if tn is not None:
                a["tmin"].append(tn)
                a["mint"] = min(a["mint"], tn)
            a["precip"] += pr or 0
            a["rain"] += int(float(row.get("has_rain", 0)))
            a["ext"] += int(float(row.get("has_hail", 0))) + int(float(row.get("has_thunder", 0)))
            a["heat"] += 1 if tm is not None and tm >= 35 else 0
            a["cold"] += 1 if tn is not None and tn <= -10 else 0
            a["frost"] += int(float(row.get("has_frost", 0)))
            a["snow"] += int(float(row.get("has_snow", 0)))
            a["thunder"] += int(float(row.get("has_thunder", 0)))
            a["obs"] += 1
            try:
                a["lat"] = float(row.get("latitude", 0))
                a["lon"] = float(row.get("longitude", 0))
            except ValueError:
                pass
            total += 1

    print(f"[聚合] {total} 行 → {len(agg)} 聚合组")

    # 写入 MySQL
    conn = DB_CONFIG.copy()
    db = pymysql.connect(**conn)
    cur = db.cursor()

    # DWS
    cur.execute("DELETE FROM dws_station_monthly WHERE year=%s", (year,))
    sql = textwrap.dedent("""\
        INSERT INTO dws_station_monthly
        (station_id,station_name,year,obs_month,latitude,longitude,
         avg_temp,avg_temp_max,avg_temp_min,max_temp,min_temp,
         total_precip,rainy_days,extreme_days,heat_wave_days,cold_wave_days,
         frost_days,snow_days,thunder_days,obs_days,climate_zone)
        VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""")

    batch = []
    for (sid, yr, mon), a in agg.items():
        avg_t = sum(a["temps"]) / len(a["temps"]) if a["temps"] else 0
        avg_tmax = sum(a["tmax"]) / len(a["tmax"]) if a["tmax"] else 0
        avg_tmin = sum(a["tmin"]) / len(a["tmin"]) if a["tmin"] else 0

        # 气候带分类
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

        batch.append((
            sid, a["name"][:200], yr, mon, round(a["lat"], 4), round(a["lon"], 4),
            round(avg_t, 1), round(avg_tmax, 1), round(avg_tmin, 1),
            round(a["maxt"], 1), round(a["mint"], 1), round(a["precip"], 1),
            a["rain"], a["ext"], a["heat"], a["cold"],
            a["frost"], a["snow"], a["thunder"], a["obs"], zone,
        ))
        if len(batch) >= 500:
            cur.executemany(sql, batch)
            batch = []
    if batch:
        cur.executemany(sql, batch)

    # ADS
    cur.execute("DELETE FROM ads_kpi WHERE data_year=%s", (year,))
    cur.execute("""SELECT AVG(avg_temp),COUNT(DISTINCT station_id),
        SUM(extreme_days)*100.0/SUM(obs_days),MAX(max_temp)
        FROM dws_station_monthly WHERE year=%s""", (year,))
    avg_t, stns, ext_pct, htemp = cur.fetchone()
    cur.executemany("INSERT INTO ads_kpi VALUES(%s,%s,%s,%s,%s)", [
        ("global_avg_temp", round(float(avg_t or 0), 2), "°C", "全球年平均温度", year),
        ("total_stations", int(stns or 0), "个", "活跃气象站总数", year),
        ("extreme_event_pct", round(float(ext_pct or 0), 2), "%", "极端天气日数占比", year),
        ("hottest_station_temp", round(float(htemp or 0), 1), "°C", "年度最高气温", year),
    ])

    cur.execute("DELETE FROM ads_monthly_trend WHERE data_year=%s", (year,))
    cur.execute("""INSERT INTO ads_monthly_trend(data_year,obs_month,avg_temp,avg_max,avg_min)
        SELECT %s,obs_month,AVG(avg_temp),AVG(avg_temp_max),AVG(avg_temp_min)
        FROM dws_station_monthly WHERE year=%s GROUP BY obs_month""", (year, year))

    cur.execute("DELETE FROM ads_ranking WHERE data_year=%s", (year,))
    for cat, order in [("hottest", "AVG(avg_temp_max) DESC"), ("coldest", "AVG(avg_temp_min) ASC"),
                        ("rainiest", "SUM(total_precip) DESC"), ("most_extreme", "SUM(extreme_days) DESC")]:
        cur.execute(f"""SELECT station_id,station_name,ROUND({order.split()[0]},1)
            FROM dws_station_monthly WHERE year=%s GROUP BY 1,2 ORDER BY 3 {order.split()[1]} LIMIT 15""", (year,))
        for i, row in enumerate(cur.fetchall()):
            cur.execute("INSERT INTO ads_ranking(category,data_year,rank_num,station_id,station_name,value) VALUES(%s,%s,%s,%s,%s,%s)",
                        (cat, year, i + 1, row[0], row[1], float(row[2])))

    cur.execute("DELETE FROM ads_zones WHERE data_year=%s", (year,))
    cur.execute("""SELECT climate_zone,COUNT(DISTINCT station_id)
        FROM dws_station_monthly WHERE year=%s GROUP BY 1""", (year,))
    for zone, cnt in cur.fetchall():
        cur.execute("INSERT INTO ads_zones VALUES(%s,%s,%s)", (year, zone, cnt))

    # 气候带趋势 ADS 表（加速趋势/气候带页面）
    cur.execute("DELETE FROM ads_zone_trends WHERE data_year=%s", (year,))
    cur.execute("""SELECT climate_zone,ROUND(AVG(avg_temp),1),ROUND(AVG(total_precip),1),
        SUM(extreme_days),SUM(heat_wave_days),SUM(cold_wave_days),COUNT(DISTINCT station_id)
        FROM dws_station_monthly WHERE year=%s GROUP BY climate_zone""", (year,))
    for row in cur.fetchall():
        cur.execute("INSERT INTO ads_zone_trends VALUES(%s,%s,%s,%s,%s,%s,%s,%s)",
                    (year, row[0], row[1], row[2], row[3], row[4], row[5], row[6]))

    # 站点概要 ADS 表（加速地图/预警页面）
    cur.execute("DELETE FROM ads_stations WHERE data_year=%s", (year,))
    cur.execute("""SELECT station_id,MAX(station_name),ROUND(AVG(latitude),4),ROUND(AVG(longitude),4),
        MAX(climate_zone),ROUND(AVG(avg_temp),1),ROUND(SUM(total_precip),1),
        SUM(heat_wave_days+cold_wave_days+extreme_days),
        SUM(heat_wave_days),SUM(cold_wave_days),SUM(extreme_days),
        SUM(frost_days),SUM(snow_days),SUM(thunder_days)
        FROM dws_station_monthly WHERE year=%s GROUP BY station_id""", (year,))
    for row in cur.fetchall():
        cur.execute("INSERT INTO ads_stations VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    (year, row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7],
                     row[8], row[9], row[10], row[11], row[12], row[13]))

    db.commit()
    db.close()
    print(f"[MySQL] {year} done")


# ═══════════════════════════════════════════
#  工具函数
# ═══════════════════════════════════════════
def _clean_float(v):
    if v is None:
        return None
    v = str(v).strip()
    if v in ("999.9", "9999.9", "99.99", "999.99", ""):
        return None
    try:
        return float(v)
    except ValueError:
        return None

def _safe_float(v):
    if v is None or v == "":
        return None
    try:
        n = float(v)
        return None if not (-90 <= n <= 60) else n
    except (ValueError, TypeError):
        return None

def _f_to_c(f):
    return round((f - 32) * 5 / 9, 1)

def _inch_to_mm(inch):
    return round(inch * 25.4, 1)

def _parse_flags(s):
    s = s.strip().ljust(6, "0")
    return {"frost": int(s[0]), "rain": int(s[1]), "snow": int(s[2]),
            "hail": int(s[3]), "thunder": int(s[4]), "tornado": int(s[5])}


# ═══════════════════════════════════════════
#  主流程
# ═══════════════════════════════════════════
def main():
    parser = argparse.ArgumentParser(description="ClimateInsight 数据加载器")
    parser.add_argument("--year", "-y", type=int, default=2024, help="年份")
    parser.add_argument("--skip-download", action="store_true", help="跳过下载，使用已有的 tar.gz")
    args = parser.parse_args()

    year = args.year
    print(f"\n{'='*50}")
    print(f"ClimateInsight 数据加载 — {year} 年")
    print(f"{'='*50}\n")

    # 步骤 1: 下载
    tar_path = RAW_DIR / f"{year}.tar.gz"
    if not args.skip_download:
        tar_path = download_year(year)
    else:
        if not tar_path.exists():
            print(f"[错误] 文件不存在: {tar_path}，请先下载")
            sys.exit(1)

    # 步骤 2: 提取合并
    csv_path = extract_and_merge(tar_path, year)

    # 步骤 3: 加载到 MySQL
    load_to_mysql(csv_path, year)

    print(f"\n{'='*50}")
    print(f"[OK] {year} done")
    print(f"   http://localhost:8080")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
