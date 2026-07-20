-- ============================================================
-- ClimateInsight DWS ETL v2 (简化修复版)
-- ============================================================
USE climate_dw;

SET hive.exec.dynamic.partition=true;
SET hive.exec.dynamic.partition.mode=nonstrict;

DROP TABLE IF EXISTS dws_station_monthly;

CREATE TABLE dws_station_monthly (
    station_id       STRING,
    station_name     STRING,
    obs_month        INT,
    avg_temp         DOUBLE,
    avg_temp_max     DOUBLE,
    avg_temp_min     DOUBLE,
    max_temp         DOUBLE,
    min_temp         DOUBLE,
    total_precip     DOUBLE,
    rainy_days       INT,
    extreme_days     INT,
    heat_wave_days   INT,
    cold_wave_days   INT,
    frost_days       INT,
    snow_days        INT,
    thunder_days     INT,
    obs_days         INT,
    climate_zone     STRING
)
COMMENT '气象站月度汇总'
PARTITIONED BY (year INT)
STORED AS ORC;

INSERT OVERWRITE TABLE dws_station_monthly PARTITION(year)
SELECT
    station_id,
    MAX(station_name),
    obs_month,
    ROUND(AVG(temp_mean), 1),
    ROUND(AVG(temp_max), 1),
    ROUND(AVG(temp_min), 1),
    ROUND(MAX(temp_max), 1),
    ROUND(MIN(temp_min), 1),
    ROUND(SUM(precip), 1),
    SUM(is_rainy),
    SUM(is_extreme),
    SUM(is_heat_wave),
    SUM(is_cold_wave),
    SUM(has_frost),
    SUM(has_snow),
    SUM(has_thunder),
    COUNT(*),
    CASE 
        WHEN AVG(temp_mean) >= 18 AND MIN(temp_min) >= 18 THEN 'tropical'
        WHEN AVG(temp_mean) >= 10 AND AVG(temp_mean) < 18 THEN 'temperate'
        WHEN ABS(MAX(latitude)) >= 60 THEN 'polar'
        WHEN AVG(precip) < 30 THEN 'arid'
        ELSE 'continental'
    END,
    year
FROM dwd_climate_daily
WHERE quality = 'valid'
GROUP BY station_id, obs_month, year;
