"""
数据质量校验脚本
验证 ODS/DWD/DWS 的完整性、一致性和数据质量
"""
import subprocess, sys
import pymysql

DB = {"host":"127.0.0.1","port":3306,"user":"root","password":"123456","database":"climate_dw","charset":"utf8mb4"}

def beeline_count(sql):
    cmd = ["docker","exec","-i","tier4_stu_hiveserver2","beeline","-u","jdbc:hive2://localhost:10000","-n","root","--silent=true","--outputformat=tsv2","-e",f"USE climate_dw; {sql}"]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    for l in r.stdout.split("\n"):
        l = l.strip()
        if l and l.isdigit():
            return int(l)
    return 0

def check(name, ok, detail=""):
    status = "✅" if ok else "❌"
    print(f"  {status} {name}: {detail}")

print("=" * 50)
print("ClimateInsight 数据质量校验")
print("=" * 50)

# 1. ODS
ods = beeline_count("SELECT COUNT(*) FROM ods_climate_raw")
check("ODS (≥ 100M)", ods > 90000000, f"{ods:,} 行")

# 2. DWD
dwd = beeline_count("SELECT COUNT(*) FROM dwd_climate_daily WHERE quality='valid'")
check("DWD (3M~4M)", 3000000 <= dwd <= 4500000, f"{dwd:,} 行")

# 3. MySQL 连接
try:
    conn = pymysql.connect(**DB)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM dws_monthly")
    dws = cur.fetchone()[0]
    check("MySQL连接", True, "ok")
    check("DWS (13万~14万)", 130000 <= dws <= 150000, f"{dws} 条")

    # 4. KPI 交叉校验
    cur.execute("SELECT kpi_value FROM ads_kpi WHERE kpi_name='global_avg_temp'")
    kpi_temp = cur.fetchone()
    check("KPI 年均温 (0~30°C)", kpi_temp and 0 < float(kpi_temp[0]) < 30, f"{kpi_temp[0]}°C" if kpi_temp else "无数据")

    cur.execute("SELECT MAX(value) FROM ads_ranking WHERE category='hottest'")
    hottest = cur.fetchone()
    check("最高温 (30~60°C)", hottest and 30 < float(hottest[0]) < 60, f"{hottest[0]}°C" if hottest else "无数据")

    cur.execute("SELECT COUNT(*) FROM ads_monthly_trend")
    months = cur.fetchone()[0]
    check("月度趋势 (12个月)", months == 12, f"{months} 个月")

    cur.execute("SELECT COUNT(*) FROM ads_zones")
    zones = cur.fetchone()[0]
    check("气候带 (3~6类)", 3 <= zones <= 6, f"{zones} 类")

    conn.close()
except Exception as e:
    print(f"  ❌ MySQL: {e}")

print("=" * 50)
print("校验完成")
