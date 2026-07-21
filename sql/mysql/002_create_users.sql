-- ClimateInsight 应用数据库用户创建
-- 此脚本在 MySQL Docker 容器首次初始化时自动执行 (root 身份)
-- 密码应与 .env 中 MYSQL_PASSWORD 一致，部署前请替换

CREATE USER IF NOT EXISTS 'climate_app'@'%' IDENTIFIED BY 'change-me';
GRANT SELECT, INSERT, UPDATE, DELETE ON climate_dw.* TO 'climate_app'@'%';

CREATE USER IF NOT EXISTS 'climate_reader'@'%' IDENTIFIED BY 'change-me-readonly';
GRANT SELECT ON climate_dw.* TO 'climate_reader'@'%';

FLUSH PRIVILEGES;
