-- ClimateInsight 增量升级：ADS 表主键调整为支持多年数据
-- 使用: mysql -u root -p climate_dw < sql/mysql/003_ads_year_keys.sql
-- 已有数据的库请先备份！本脚本会重建表约束。

USE climate_dw;

-- ads_kpi: 删除单列主键，改为复合主键
-- 备份: CREATE TABLE ads_kpi_bak AS SELECT * FROM ads_kpi;
ALTER TABLE ads_kpi DROP PRIMARY KEY;
ALTER TABLE ads_kpi MODIFY COLUMN kpi_name VARCHAR(50) NOT NULL;
ALTER TABLE ads_kpi MODIFY COLUMN data_year INT NOT NULL DEFAULT 2024;
ALTER TABLE ads_kpi ADD PRIMARY KEY (kpi_name, data_year);

-- ads_ranking: 增加唯一索引防止重复排名
ALTER TABLE ads_ranking MODIFY COLUMN data_year INT NOT NULL DEFAULT 2024;
ALTER TABLE ads_ranking ADD UNIQUE KEY IF NOT EXISTS uk_ranking (category, data_year, rank_num);

-- ads_monthly_trend: 重建为复合主键
-- 备份: CREATE TABLE ads_monthly_trend_bak AS SELECT * FROM ads_monthly_trend;
ALTER TABLE ads_monthly_trend DROP PRIMARY KEY;
ALTER TABLE ads_monthly_trend MODIFY COLUMN data_year INT NOT NULL DEFAULT 2024;
ALTER TABLE ads_monthly_trend ADD PRIMARY KEY (data_year, obs_month);

-- ads_zones: 重建为复合主键
-- 备份: CREATE TABLE ads_zones_bak AS SELECT * FROM ads_zones;
ALTER TABLE ads_zones DROP PRIMARY KEY;
ALTER TABLE ads_zones MODIFY COLUMN data_year INT NOT NULL DEFAULT 2024;
ALTER TABLE ads_zones ADD PRIMARY KEY (data_year, climate_zone);

-- 验证
SHOW CREATE TABLE ads_kpi\G
SHOW CREATE TABLE ads_ranking\G
SHOW CREATE TABLE ads_monthly_trend\G
SHOW CREATE TABLE ads_zones\G
