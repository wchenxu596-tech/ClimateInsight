"""
数据质量校验脚本 v2 — 环境变量配置 + 动态阈值 + 年份过滤
用法: MYSQL_PASSWORD=xxx python scripts/verify_data.py [--year 2024]
"""
import subprocess, sys, os, argparse
import pymysql

# ── 配置(环境变量) ──
DB = {
    "host": os.getenv("MYSQL_HOST", "127.0.0.1"),
    "port": int(os.getenv("MYSQL_PORT", "3306")),
    "user": os.getenv("MYSQL_USER", "climate_app"),
    "password": os.environ["MYSQL_PASSWORD"],
    "database": os.getenv("MYSQL_DATABASE", "climate_dw"),
    "charset": "utf8mb4",
}
HIVE_CONTAINER = os.getenv("HIVE_CONTAINER", "hive-server")
HIVE_JDBC_URL = os.getenv("HIVE_JDBC_URL", "jdbc:hive2://hive-server:10000")

# 合理常数 (2024年)
STATION_COUNT = 12160
DAYS_IN_YEAR = 366
MAX_ODS_ROWS = STATION_COUNT * DAYS_IN_YEAR  # ~4.45M

def beeline_count(sql):
    cmd = ["docker","exec","-i", HIVE_CONTAINER, "beeline",
           "-u", HIVE_JDBC_URL, "-n","root","--silent=true","--outputformat=tsv2",
           "-e", f"USE climate_dw; {sql}"]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    for l in r.stdout.split("\n"):
        l = l.strip()
        if l and l.isdigit():
            return int(l)
    return 0

def check(name, ok, detail=""):
    status = "\u2705" if ok else "\u274c"
    print(f"  {status} {name}: {detail}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, default=2024)
    args = parser.parse_args()
    year = args.year

    print("=" * 50)
    print(f"ClimateInsight 数据质量校验 — year={year}")
    print("=" * 50)

    # 1. ODS
    ods = beeline_count("SELECT COUNT(*) FROM ods_climate_raw")
    check("ODS 行数合理", 0 < ods <= MAX_ODS_ROWS, f"{ods:,}/{MAX_ODS_ROWS:,}")

    # 2. DWD
    dwd = beeline_count("SELECT COUNT(*) FROM dwd_climate_daily WHERE quality='valid'")
    check("DWD (3M~4.5M)", 3000000 <= dwd <= 4500000, f"{dwd:,} 行")

    # 3. MySQL 连接 + 各项校验
    try:
        conn = pymysql.connect(**DB)
        cur = conn.cursor()

        # 3a. DWS 行数
        cur.execute("SELECT COUNT(*) FROM dws_station_monthly WHERE year=%s", (year,))
        dws = cur.fetchone()[0]
        check("MySQL连接", True, "ok")
        check("DWS (13万~14万)", 130000 <= dws <= 150000, f"{dws:,} 条")

        # 3b. DWS 主键唯一性
        cur.execute("""SELECT COUNT(*) FROM (
            SELECT station_id, year, obs_month, COUNT(*) AS cnt
            FROM dws_station_monthly WHERE year=%s
            GROUP BY station_id, year, obs_month HAVING cnt > 1
        ) dup""", (year,))
        dup_count = cur.fetchone()[0]
        check("DWS 主键唯一", dup_count == 0, f"重复组数: {dup_count}")

        # 3c. DWS 温度范围
        cur.execute("""SELECT COUNT(*) FROM dws_station_monthly
            WHERE year=%s AND (avg_temp NOT BETWEEN -90 AND 60 OR max_temp NOT BETWEEN -90 AND 60)""", (year,))
        bad_temp = cur.fetchone()[0]
        check("DWS 温度范围 (-90~60°C)", bad_temp == 0, f"异常: {bad_temp} 条")

        # 3d. KPI 交叉校验
        cur.execute("SELECT kpi_value FROM ads_kpi WHERE kpi_name='global_avg_temp' AND data_year=%s", (year,))
        kpi_temp = cur.fetchone()
        check("KPI 年均温 (0~30°C)", kpi_temp and 0 < float(kpi_temp[0]) < 30,
              f"{kpi_temp[0]}°C" if kpi_temp else "无数据")

        cur.execute("SELECT MAX(value) FROM ads_ranking WHERE category='hottest' AND data_year=%s", (year,))
        hottest = cur.fetchone()
        check("最高温 (30~60°C)", hottest and 30 < float(hottest[0]) < 60,
              f"{hottest[0]}°C" if hottest else "无数据")

        # 3e. ADS 月度完整
        cur.execute("SELECT COUNT(*) FROM ads_monthly_trend WHERE data_year=%s", (year,))
        months = cur.fetchone()[0]
        check("月度趋势 (12个月)", months == 12, f"{months} 个月")

        # 3f. 排名完整
        cur.execute("SELECT category, COUNT(*) FROM ads_ranking WHERE data_year=%s GROUP BY category", (year,))
        rank_counts = cur.fetchall()
        for cat, cnt in rank_counts:
            check(f"排名 {cat} (15条)", cnt == 15, f"{cnt} 条")

        # 3g. 气候带
        cur.execute("SELECT COUNT(*) FROM ads_zones WHERE data_year=%s", (year,))
        zones = cur.fetchone()[0]
        check("气候带 (3~6类)", 3 <= zones <= 6, f"{zones} 类")

        conn.close()
    except Exception as e:
        print(f"  \u274c MySQL: {e}")

    print("=" * 50)
    print("校验完成")

if __name__ == "__main__":
    main()
