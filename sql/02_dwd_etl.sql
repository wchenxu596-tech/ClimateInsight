-- ============================================================
-- ClimateInsight DWD ETL v4 — OpenCSVSerde已处理引号，无需REGEXP_REPLACE
-- ============================================================

USE climate_dw;

SET hive.exec.dynamic.partition=true;
SET hive.exec.dynamic.partition.mode=nonstrict;
SET hive.exec.max.dynamic.partitions=2000;
SET hive.exec.max.dynamic.partitions.pernode=2000;

DROP TABLE IF EXISTS dwd_climate_daily;

CREATE TABLE dwd_climate_daily (
    station_id      STRING,   station_name STRING,   obs_date STRING,
    latitude        DOUBLE,   longitude DOUBLE,      elevation DOUBLE,
    temp_mean       DOUBLE,   temp_max DOUBLE,       temp_min DOUBLE,
    temp_range      DOUBLE,   dew_point DOUBLE,      precip DOUBLE,
    is_rainy        INT,      is_heavy_rain INT,     wind_speed DOUBLE,
    wind_gust       DOUBLE,   pressure DOUBLE,       visibility DOUBLE,
    has_frost       INT,      has_rain INT,          has_snow INT,
    has_hail        INT,      has_thunder INT,       has_tornado INT,
    is_heat_wave    INT,      is_cold_wave INT,      is_extreme INT,
    obs_month       INT,      season STRING,         quality STRING
)
COMMENT '全球气候观测数据明细表(清洗后)'
PARTITIONED BY (year INT)
STORED AS ORC;

INSERT OVERWRITE TABLE dwd_climate_daily PARTITION(year)
SELECT
    station_id,
    TRIM(station_name)                                              AS station_name,
    obs_date,
    CAST(latitude AS DOUBLE),     CAST(longitude AS DOUBLE),       CAST(elevation AS DOUBLE),
    
    ROUND((CAST(temp_mean AS DOUBLE) - 32) * 5 / 9, 1)            AS temp_mean,
    ROUND((CAST(temp_max AS DOUBLE)  - 32) * 5 / 9, 1)            AS temp_max,
    ROUND((CAST(temp_min AS DOUBLE)  - 32) * 5 / 9, 1)            AS temp_min,
    ROUND((CAST(temp_max AS DOUBLE)  - CAST(temp_min AS DOUBLE)) * 5 / 9, 1) AS temp_range,
    ROUND((CAST(dew_point AS DOUBLE) - 32) * 5 / 9, 1)            AS dew_point,
    
    ROUND(CAST(precip AS DOUBLE) * 25.4, 1)                        AS precip,
    CASE WHEN CAST(precip AS DOUBLE) > 0 THEN 1 ELSE 0 END         AS is_rainy,
    CASE WHEN CAST(precip AS DOUBLE) * 25.4 >= 25 THEN 1 ELSE 0 END AS is_heavy_rain,
    
    CAST(wind_speed AS DOUBLE),    CAST(wind_gust AS DOUBLE),
    CAST(pressure_slp AS DOUBLE),  CAST(visibility AS DOUBLE),
    
    CAST(SUBSTR(weather_flags, 1, 1) AS INT) AS has_frost,
    CAST(SUBSTR(weather_flags, 2, 1) AS INT) AS has_rain,
    CAST(SUBSTR(weather_flags, 3, 1) AS INT) AS has_snow,
    CAST(SUBSTR(weather_flags, 4, 1) AS INT) AS has_hail,
    CAST(SUBSTR(weather_flags, 5, 1) AS INT) AS has_thunder,
    CAST(SUBSTR(weather_flags, 6, 1) AS INT) AS has_tornado,
    
    CASE WHEN ROUND((CAST(temp_max AS DOUBLE) - 32) * 5 / 9, 1) >= 35 THEN 1 ELSE 0 END AS is_heat_wave,
    CASE WHEN ROUND((CAST(temp_min AS DOUBLE) - 32) * 5 / 9, 1) <= -10 THEN 1 ELSE 0 END AS is_cold_wave,
    CASE WHEN ROUND((CAST(temp_max AS DOUBLE) - 32) * 5 / 9, 1) >= 35 
          OR ROUND((CAST(temp_min AS DOUBLE) - 32) * 5 / 9, 1) <= -10
          OR CAST(precip AS DOUBLE) * 25.4 >= 25 THEN 1 ELSE 0 END AS is_extreme,
    
    CAST(SUBSTR(obs_date, 6, 2) AS INT) AS obs_month,
    CASE WHEN CAST(SUBSTR(obs_date, 6, 2) AS INT) IN (3,4,5)  THEN 'spring'
         WHEN CAST(SUBSTR(obs_date, 6, 2) AS INT) IN (6,7,8)  THEN 'summer'
         WHEN CAST(SUBSTR(obs_date, 6, 2) AS INT) IN (9,10,11) THEN 'autumn'
         ELSE 'winter' END AS season,
    
    CASE WHEN temp_mean IN ('9999.9','') THEN 'suspicious' ELSE 'valid' END AS quality,
    
    CAST(SUBSTR(obs_date, 1, 4) AS INT) AS year

FROM ods_climate_raw
WHERE temp_mean != '9999.9' AND temp_mean != '' AND temp_mean IS NOT NULL
  AND latitude != '0' AND latitude != '0.0';
