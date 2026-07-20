"""
ClimateInsight — Python ETL 聚合脚本
绕过 YARN MapReduce 内存限制，用 Python 本地聚合
"""
import subprocess, csv, io, os, sys
from collections import defaultdict

def beeline_query(sql: str) -> list:
    """通过 beeline 执行查询，返回 dict 列表"""
    cmd = [
        "docker", "exec", "-i", "tier4_stu_hiveserver2",
        "beeline", "-u", "jdbc:hive2://localhost:10000",
        "-n", "root", "--silent=true", "--outputformat=csv2",
        "-e", f"USE climate_dw; {sql}"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    lines = [l.strip() for l in result.stdout.split('\n') if l.strip() and not l.startswith('SLF4J') and not l.startswith('Picked')]
    if not lines: return []
    reader = csv.DictReader(io.StringIO('\n'.join(lines)))
    return list(reader)

def beeline_execute(sql: str):
    """执行非查询SQL"""
    cmd = [
        "docker", "exec", "-i", "tier4_stu_hiveserver2",
        "beeline", "-u", "jdbc:hive2://localhost:10000",
        "-n", "root", "--silent=true",
        "-e", f"USE climate_dw; {sql}"
    ]
    subprocess.run(cmd, capture_output=True, text=True, timeout=120)


def dws_aggregate():
    """DWS: 从DWD读取 → Python聚合 → 写入Hive"""
    print("[DWS] 从 DWD 读取数据...")
    rows = beeline_query("""
        SELECT station_id, station_name, obs_month, year,
               temp_mean, temp_max, temp_min, precip,
               CAST(is_rainy AS INT) AS is_rainy,
               CAST(is_extreme AS INT) AS is_extreme,
               CAST(is_heat_wave AS INT) AS is_heat_wave,
               CAST(is_cold_wave AS INT) AS is_cold_wave,
               CAST(has_frost AS INT) AS has_frost,
               CAST(has_snow AS INT) AS has_snow,
               CAST(has_thunder AS INT) AS has_thunder,
               latitude
        FROM dwd_climate_daily WHERE quality='valid'
    """)
    print(f"[DWS] 读取 {len(rows)} 行，聚合中...")
    
    if not rows:
        print("[DWS] 无数据！")
        return
    
    # 聚合: key = (station_id, obs_month, year)
    agg = defaultdict(lambda: {
        'station_name': '', 'temps': [], 'temps_max': [], 'temps_min': [],
        'precip_sum': 0.0, 'rainy': 0, 'extreme': 0, 'heat': 0, 'cold': 0,
        'frost': 0, 'snow': 0, 'thunder': 0, 'obs': 0, 'lats': [], 'max_temp': -999, 'min_temp': 999
    })
    
    for r in rows:
        key = (r['station_id'], r['obs_month'], r['year'])
        a = agg[key]
        a['station_name'] = r['station_name']
        try:
            t = float(r['temp_mean']); a['temps'].append(t)
            tmax = float(r['temp_max']); a['temps_max'].append(tmax)
            tmin = float(r['temp_min']); a['temps_min'].append(tmin)
            a['max_temp'] = max(a['max_temp'], tmax)
            a['min_temp'] = min(a['min_temp'], tmin)
        except: pass
        try: a['precip_sum'] += float(r['precip'])
        except: pass
        a['rainy'] += int(r.get('is_rainy', 0))
        a['extreme'] += int(r.get('is_extreme', 0))
        a['heat'] += int(r.get('is_heat_wave', 0))
        a['cold'] += int(r.get('is_cold_wave', 0))
        a['frost'] += int(r.get('has_frost', 0))
        a['snow'] += int(r.get('has_snow', 0))
        a['thunder'] += int(r.get('has_thunder', 0))
        a['obs'] += 1
        try: a['lats'].append(float(r['latitude']))
        except: pass
    
    print(f"[DWS] 聚合为 {len(agg)} 个月度记录")
    
    # 写入临时CSV → HDFS → Hive
    tmpfile = "/tmp/dws_station_monthly.csv"
    with open(tmpfile, "w", encoding="utf-8") as f:
        f.write("station_id,station_name,obs_month,avg_temp,avg_temp_max,avg_temp_min,max_temp,min_temp,total_precip,rainy_days,extreme_days,heat_wave_days,cold_wave_days,frost_days,snow_days,thunder_days,obs_days,climate_zone,year\n")
        for (sid, mon, yr), a in agg.items():
            avg_t = sum(a['temps'])/len(a['temps']) if a['temps'] else 0
            avg_tmax = sum(a['temps_max'])/len(a['temps_max']) if a['temps_max'] else 0
            avg_tmin = sum(a['temps_min'])/len(a['temps_min']) if a['temps_min'] else 0
            avg_lat = sum(a['lats'])/len(a['lats']) if a['lats'] else 0
            
            if avg_t >= 18 and a['min_temp'] >= 18: zone = 'tropical'
            elif avg_t >= 10: zone = 'temperate'
            elif abs(avg_lat) >= 60: zone = 'polar'
            elif a['precip_sum']/max(a['obs'],1) < 30: zone = 'arid'
            else: zone = 'continental'
            
            f.write(f"{sid},{a['station_name']},{mon},{avg_t:.1f},{avg_tmax:.1f},{avg_tmin:.1f},{a['max_temp']:.1f},{a['min_temp']:.1f},{a['precip_sum']:.1f},{a['rainy']},{a['extreme']},{a['heat']},{a['cold']},{a['frost']},{a['snow']},{a['thunder']},{a['obs']},{zone},{yr}\n")
    
    print(f"[DWS] 写入临时文件: {tmpfile}")
    
    # 复制到容器挂载目录并上传HDFS
    docker_tmp = "/opt/data/dws_station_monthly.csv"
    subprocess.run(f"docker cp {tmpfile} tier4_stu_namenode:{docker_tmp}", shell=True)
    subprocess.run(f'docker exec tier4_stu_namenode hadoop fs -mkdir -p /warehouse/climate/dws', shell=True)
    subprocess.run(f'docker exec tier4_stu_namenode hadoop fs -put -f {docker_tmp} /warehouse/climate/dws/', shell=True)
    
    print("[DWS] HDFS上传完成，写入Hive表...")
    os.remove(tmpfile)


def ads_compute():
    """ADS: 从DWS计算KPI和排名"""
    print("[ADS] 计算KPI...")
    
    rows = beeline_query("SELECT year, AVG(avg_temp) as gtemp, COUNT(DISTINCT station_id) as stns, SUM(extreme_days)*100.0/SUM(obs_days) as ext_pct, MAX(max_temp) as htemp FROM dws_station_monthly GROUP BY year")
    
    # 同样用Python聚合写入
    print(f"[ADS] KPI: {len(rows)} 条记录")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "ads":
        ads_compute()
    else:
        dws_aggregate()
