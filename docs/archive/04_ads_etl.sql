-- ============================================================
-- ClimateInsight ADS 层 ETL
-- DWS → ADS: 面向业务场景的应用数据
-- ============================================================

USE climate_dw;

-- ============================================================
-- ADS 1: ads_global_temp_trend (全球温度趋势)
-- 每年全球平均温度，用于大屏趋势图
-- ============================================================
DROP TABLE IF EXISTS ads_global_temp_trend;
CREATE TABLE ads_global_temp_trend (
    year              INT      COMMENT '年份',
    avg_temp          DOUBLE   COMMENT '全球年平均温度(°C)',
    avg_temp_max      DOUBLE   COMMENT '全球年均最高温(°C)',
    avg_temp_min      DOUBLE   COMMENT '全球年均最低温(°C)',
    total_precip      DOUBLE   COMMENT '全球年总降水(mm)',
    extreme_days_pct  DOUBLE   COMMENT '极端天气日数占比(%)',
    station_count     INT      COMMENT '有效气象站数',
    
    -- 与上一年对比
    temp_change       DOUBLE   COMMENT '温度较上年变化(°C)'
)
COMMENT '全球年度温度趋势'
STORED AS ORC;

INSERT OVERWRITE TABLE ads_global_temp_trend
SELECT
    year,
    ROUND(AVG(avg_temp), 2)               AS avg_temp,
    ROUND(AVG(avg_temp_max), 2)           AS avg_temp_max,
    ROUND(AVG(avg_temp_min), 2)           AS avg_temp_min,
    ROUND(SUM(total_precip) / COUNT(DISTINCT station_id), 0) AS total_precip,
    ROUND(SUM(extreme_days) * 100.0 / SUM(obs_days), 2) AS extreme_days_pct,
    COUNT(DISTINCT station_id)            AS station_count,
    ROUND(AVG(avg_temp) - LAG(AVG(avg_temp)) OVER (ORDER BY year), 3) AS temp_change
FROM dws_station_monthly
GROUP BY year;


-- ============================================================
-- ADS 2: ads_city_climate_ranking (城市气候排名)
-- TOP20 最热/最冷/最多雨城市，用于大屏排名
-- ============================================================
DROP TABLE IF EXISTS ads_city_climate_ranking;
CREATE TABLE ads_city_climate_ranking (
    rank_category     STRING   COMMENT '排名类别: hottest/coldest/rainiest/most_extreme',
    rank_num          INT      COMMENT '排名',
    station_id        STRING,
    station_name      STRING,
    country_hint      STRING   COMMENT '国家推测(基于坐标)',
    value             DOUBLE   COMMENT '排名值',
    latitude          DOUBLE,
    longitude         DOUBLE,
    year              INT
)
COMMENT '城市气候排名(年度)'
STORED AS ORC;

-- 最热城市 TOP20
INSERT INTO ads_city_climate_ranking
SELECT 'hottest', ROW_NUMBER() OVER (ORDER BY avg_temp DESC), 
       station_id, station_name, '', ROUND(avg_temp, 1), latitude, longitude, year
FROM dws_station_monthly WHERE obs_month IN (6,7,8) AND data_completeness > 0.7
GROUP BY station_id, station_name, latitude, longitude, year
LIMIT 20;

-- 最冷城市 TOP20
INSERT INTO ads_city_climate_ranking
SELECT 'coldest', ROW_NUMBER() OVER (ORDER BY avg_temp ASC),
       station_id, station_name, '', ROUND(avg_temp, 1), latitude, longitude, year
FROM dws_station_monthly WHERE obs_month IN (12,1,2) AND data_completeness > 0.7
GROUP BY station_id, station_name, latitude, longitude, year
LIMIT 20;

-- 最多雨城市 TOP20
INSERT INTO ads_city_climate_ranking
SELECT 'rainiest', ROW_NUMBER() OVER (ORDER BY total_precip DESC),
       station_id, station_name, '', ROUND(total_precip, 0), latitude, longitude, year
FROM dws_station_monthly WHERE data_completeness > 0.7
GROUP BY station_id, station_name, latitude, longitude, year
LIMIT 20;

-- 极端天气最多 TOP20
INSERT INTO ads_city_climate_ranking
SELECT 'most_extreme', ROW_NUMBER() OVER (ORDER BY extreme_days DESC),
       station_id, station_name, '', CAST(extreme_days AS DOUBLE), latitude, longitude, year
FROM dws_station_monthly WHERE data_completeness > 0.7
GROUP BY station_id, station_name, latitude, longitude, year
LIMIT 20;


-- ============================================================
-- ADS 3: ads_climate_kpi (大屏核心KPI)
-- 每日快照，供前端KPI卡片使用
-- ============================================================
DROP TABLE IF EXISTS ads_climate_kpi;
CREATE TABLE ads_climate_kpi (
    kpi_name          STRING   COMMENT '指标名称',
    kpi_value         DOUBLE   COMMENT '指标值',
    kpi_unit          STRING   COMMENT '单位',
    kpi_trend         STRING   COMMENT '趋势: up/down/flat',
    kpi_desc          STRING   COMMENT '指标说明',
    year              INT
)
COMMENT '大屏核心KPI快照'
STORED AS ORC;

-- 汇总计算（以最新年份为基准）
INSERT INTO ads_climate_kpi
SELECT 'global_avg_temp',      ROUND(AVG(avg_temp), 2), '°C',
       CASE WHEN AVG(avg_temp) > LAG(AVG(avg_temp)) OVER (ORDER BY year) THEN 'up' ELSE 'down' END,
       '全球年平均温度', year
FROM dws_station_monthly GROUP BY year;

INSERT INTO ads_climate_kpi  
SELECT 'total_stations',       COUNT(DISTINCT station_id), '个',
       'flat', '活跃气象站总数', year
FROM dws_station_monthly GROUP BY year;

INSERT INTO ads_climate_kpi
SELECT 'extreme_event_pct',    ROUND(SUM(extreme_days)*100.0/SUM(obs_days), 2), '%',
       CASE WHEN SUM(extreme_days)*100.0/SUM(obs_days) > 
                 LAG(SUM(extreme_days)*100.0/SUM(obs_days)) OVER (ORDER BY year) THEN 'up' ELSE 'down' END,
       '极端天气日数占比', year
FROM dws_station_monthly GROUP BY year;

INSERT INTO ads_climate_kpi
SELECT 'hottest_station_temp', ROUND(MAX(max_temp), 1), '°C',
       'flat', '年度最高气温', year
FROM dws_station_monthly GROUP BY year;


-- ============================================================
-- 校验查询
-- ============================================================
SELECT '=== 全链路校验 ===' AS info;
SELECT 'ODS分区数', COUNT(DISTINCT year) FROM ods_climate_daily;
SELECT 'DWD行数', COUNT(*) FROM dwd_climate_daily;
SELECT 'DWS行数', COUNT(*) FROM dws_station_monthly;
SELECT 'ADS趋势行数', COUNT(*) FROM ads_global_temp_trend;
SELECT 'ADS排名行数', COUNT(*) FROM ads_city_climate_ranking;
SELECT 'ADSKPI行数', COUNT(*) FROM ads_climate_kpi;
