-- ClimateInsight MySQL Schema v1
-- 执行: mysql -u root -p < sql/mysql/001_schema.sql

CREATE DATABASE IF NOT EXISTS climate_dw CHARACTER SET utf8mb4;
USE climate_dw;

-- DWS: 气象站月度汇总
DROP TABLE IF EXISTS dws_station_monthly;
CREATE TABLE dws_station_monthly (
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
    obs_days     INT DEFAULT 0,
    climate_zone VARCHAR(20),
    PRIMARY KEY (station_id, year, obs_month),
    INDEX idx_year_month (year, obs_month),
    INDEX idx_climate_zone (year, climate_zone),
    INDEX idx_temp_max (year, avg_temp_max),
    INDEX idx_precip (year, total_precip)
) ENGINE=InnoDB;

-- ADS: KPI 看板
DROP TABLE IF EXISTS ads_kpi;
CREATE TABLE ads_kpi (
    kpi_name  VARCHAR(50) PRIMARY KEY,
    kpi_value DOUBLE,
    kpi_unit  VARCHAR(20),
    kpi_desc  VARCHAR(200),
    data_year INT DEFAULT 2024
) ENGINE=InnoDB;

-- ADS: 城市排名
DROP TABLE IF EXISTS ads_ranking;
CREATE TABLE ads_ranking (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    category     VARCHAR(20) NOT NULL,
    rank_num     INT,
    station_id   VARCHAR(20),
    station_name VARCHAR(200),
    value        DOUBLE,
    data_year    INT DEFAULT 2024,
    INDEX idx_cat_year (category, data_year)
) ENGINE=InnoDB;

-- ADS: 月度趋势
DROP TABLE IF EXISTS ads_monthly_trend;
CREATE TABLE ads_monthly_trend (
    obs_month INT PRIMARY KEY,
    avg_temp  DOUBLE,
    avg_max   DOUBLE,
    avg_min   DOUBLE,
    data_year INT DEFAULT 2024
) ENGINE=InnoDB;

-- ADS: 气候带分布
DROP TABLE IF EXISTS ads_zones;
CREATE TABLE ads_zones (
    climate_zone  VARCHAR(20) PRIMARY KEY,
    station_count INT,
    data_year     INT DEFAULT 2024
) ENGINE=InnoDB;
