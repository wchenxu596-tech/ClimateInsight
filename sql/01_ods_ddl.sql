-- ============================================================
-- ClimateInsight: 全球气候智能分析平台
-- ODS 层 — 原始NOAA GSOD数据 (28列，与源文件完全一致)
-- ============================================================

CREATE DATABASE IF NOT EXISTS climate_dw
  COMMENT '全球气候数据仓库'
  LOCATION '/user/hive/warehouse/climate_dw.db';

USE climate_dw;

-- ============================================================
-- ODS: ods_climate_raw (外部表，28列，按year分区)
-- 数据直接来自 NOAA GSOD CSV，不做任何转换
-- ============================================================
DROP TABLE IF EXISTS ods_climate_raw;
CREATE EXTERNAL TABLE ods_climate_raw (
    station_id        STRING  COMMENT '气象站ID',
    obs_date          STRING  COMMENT '观测日期 yyyy-MM-dd',
    latitude          STRING  COMMENT '纬度',
    longitude         STRING  COMMENT '经度',
    elevation         STRING  COMMENT '海拔(米)',
    station_name      STRING  COMMENT '气象站名称',
    temp_mean         STRING  COMMENT '日平均温度(°F)',
    temp_attr         STRING  COMMENT '温度观测标记',
    dew_point         STRING  COMMENT '露点(°F)',
    dew_attr          STRING  COMMENT '露点观测标记',
    pressure_slp      STRING  COMMENT '海平面气压',
    slp_attr          STRING  COMMENT '气压观测标记',
    pressure_stp      STRING  COMMENT '站点气压',
    stp_attr          STRING  COMMENT '站点气压标记',
    visibility         STRING  COMMENT '能见度',
    vis_attr          STRING  COMMENT '能见度标记',
    wind_speed        STRING  COMMENT '风速',
    wdsp_attr         STRING  COMMENT '风速标记',
    wind_max          STRING  COMMENT '最大风速',
    wind_gust         STRING  COMMENT '阵风',
    temp_max          STRING  COMMENT '日最高温度(°F)',
    max_attr          STRING  COMMENT '最高温标记',
    temp_min          STRING  COMMENT '日最低温度(°F)',
    min_attr          STRING  COMMENT '最低温标记',
    precip            STRING  COMMENT '降水量(英寸)',
    prcp_attr         STRING  COMMENT '降水标记',
    snow_depth        STRING  COMMENT '积雪深度',
    weather_flags     STRING  COMMENT '气象标记(FRSHTT)'
)
COMMENT '全球气候观测原始数据 (NOAA GSOD 28列原始格式)'
PARTITIONED BY (year STRING COMMENT '年份')
ROW FORMAT DELIMITED FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION '/warehouse/climate/ods'
TBLPROPERTIES ('skip.header.line.count'='1');
