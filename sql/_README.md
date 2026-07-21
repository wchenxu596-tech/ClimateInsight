# SQL Scripts

## Hive (大数据平台)

执行顺序:

```
01_ods_ddl.sql → 02_dwd_etl.sql
```

- `01_ods_ddl.sql` — 创建 ODS 外部表
- `02_dwd_etl.sql` — ODS → DWD 清洗转换

> 注意: DWS/ADS 不再通过 Hive SQL 生成，改由 `scripts/etl_to_mysql.py` 通过 Python 聚合后写入 MySQL。

## MySQL (应用数据库)

初始化顺序 (空库):

```
mysql/001_init.sql
```

增量升级 (已有数据):

```
mysql/002_add_dws_weather_days.sql   (增加天气日字段)
mysql/003_ads_year_keys.sql          (修复ADS复合主键)
```
