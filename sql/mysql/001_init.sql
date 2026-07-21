-- ClimateInsight MySQL 初始化脚本（空库建表）
-- 使用: mysql -u root -p < sql/mysql/001_init.sql
-- 注意：本脚本仅在空库上执行；已有数据的库请使用增量升级脚本 002/003

CREATE DATABASE IF NOT EXISTS climate_dw CHARACTER SET utf8mb4;
USE climate_dw;

-- DWS: 气象站月度汇总
CREATE TABLE IF NOT EXISTS dws_station_monthly (
    station_id   VARCHAR(20) NOT NULL,
    station_name VARCHAR(200),
    year         INT NOT NULL DEFAULT 2024,
    obs_month    INT NOT NULL,
    latitude     DOUBLE,
    longitude    DOUBLE,
    avg_temp     DOUBLE,
    avg_temp_max DOUBLE,
    avg_temp_min DOUBLE,
    max_temp     DOUBLE,
    min_temp     DOUBLE,
    total_precip DOUBLE,
    rainy_days   INT DEFAULT 0,
    extreme_days INT DEFAULT 0,
    heat_wave_days INT DEFAULT 0,
    cold_wave_days INT DEFAULT 0,
    frost_days     INT DEFAULT 0,
    snow_days      INT DEFAULT 0,
    thunder_days   INT DEFAULT 0,
    obs_days     INT DEFAULT 0,
    climate_zone VARCHAR(20),
    PRIMARY KEY (station_id, year, obs_month),
    INDEX idx_year_month (year, obs_month),
    INDEX idx_climate_zone (year, climate_zone),
    INDEX idx_temp_max (year, avg_temp_max),
    INDEX idx_precip (year, total_precip)
) ENGINE=InnoDB;

-- ADS: KPI 看板（复合主键支持多年）
CREATE TABLE IF NOT EXISTS ads_kpi (
    kpi_name  VARCHAR(50) NOT NULL,
    kpi_value DOUBLE,
    kpi_unit  VARCHAR(20),
    kpi_desc  VARCHAR(200),
    data_year INT NOT NULL DEFAULT 2024,
    PRIMARY KEY (kpi_name, data_year)
) ENGINE=InnoDB;

-- ADS: 城市排名
CREATE TABLE IF NOT EXISTS ads_ranking (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    category     VARCHAR(20) NOT NULL,
    rank_num     INT,
    station_id   VARCHAR(20),
    station_name VARCHAR(200),
    value        DOUBLE,
    data_year    INT NOT NULL DEFAULT 2024,
    UNIQUE KEY uk_ranking (category, data_year, rank_num),
    INDEX idx_cat_year (category, data_year)
) ENGINE=InnoDB;

-- ADS: 月度趋势（复合主键支持多年）
CREATE TABLE IF NOT EXISTS ads_monthly_trend (
    data_year INT NOT NULL DEFAULT 2024,
    obs_month INT NOT NULL,
    avg_temp  DOUBLE,
    avg_max   DOUBLE,
    avg_min   DOUBLE,
    PRIMARY KEY (data_year, obs_month)
) ENGINE=InnoDB;

-- ADS: 气候带分布（复合主键支持多年）
CREATE TABLE IF NOT EXISTS ads_zones (
    data_year     INT NOT NULL DEFAULT 2024,
    climate_zone  VARCHAR(20) NOT NULL,
    station_count INT,
    PRIMARY KEY (data_year, climate_zone)
) ENGINE=InnoDB;
