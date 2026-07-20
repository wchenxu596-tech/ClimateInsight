# Hive SQL Scripts

按执行顺序：
1. `01_ods_ddl.sql` - ODS 层建表 + 数据加载
2. `02_dwd_ddl.sql` - DWD 层清洗 + 维度表
3. `03_dws_ddl.sql` - DWS 层汇总
4. `04_ads_ddl.sql` - ADS 层应用表 (RFM/关联规则/KPI)
5. `10_etl_run.sql` - 全链路 ETL 执行脚本
