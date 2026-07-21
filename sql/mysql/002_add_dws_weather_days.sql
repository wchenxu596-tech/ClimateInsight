-- ClimateInsight 增量升级：为 dws_station_monthly 增加天气日字段
-- 使用: mysql -u root -p climate_dw < sql/mysql/002_add_dws_weather_days.sql
-- 已有数据的库请使用此脚本，不要执行 001_init.sql

USE climate_dw;

ALTER TABLE dws_station_monthly
  ADD COLUMN IF NOT EXISTS heat_wave_days INT DEFAULT 0 AFTER extreme_days,
  ADD COLUMN IF NOT EXISTS cold_wave_days INT DEFAULT 0 AFTER heat_wave_days,
  ADD COLUMN IF NOT EXISTS frost_days     INT DEFAULT 0 AFTER cold_wave_days,
  ADD COLUMN IF NOT EXISTS snow_days      INT DEFAULT 0 AFTER frost_days,
  ADD COLUMN IF NOT EXISTS thunder_days   INT DEFAULT 0 AFTER snow_days;

-- 验证
DESCRIBE dws_station_monthly;
