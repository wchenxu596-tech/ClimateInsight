# ClimateInsight — 全球气候智能分析平台

基于 NOAA GSOD 数据的 2024 年全球气候数据仓库与 BI 分析系统。

> ⚠️ **当前数据范围**：仅包含 2024 年数据。多年趋势需导入更多年份后开放。

## 架构

```
NOAA GSOD CSV → Hive(ODS→DWD) → Python聚合 → MySQL(DWS/ADS) → Flask API → Vue3大屏
```

## 快速启动

```bash
# 1. 启动基础设施 (需要预先运行的 Hadoop+Hive+MySQL Docker 容器)
docker start tier4_stu_namenode tier4_stu_hiveserver2 tier4_stu_mysql ...

# 2. 初始化 MySQL 表 + 运行 ETL
python scripts/etl_to_mysql.py

# 3. 数据校验
python scripts/verify_data.py

# 4. 启动后端
cd backend && python app.py           # http://localhost:5000

# 5. 启动前端
cd frontend && npm install && npm run dev   # http://localhost:5173
```

## API

| 接口 | 说明 |
|------|------|
| `GET /api/health` | 健康检查 |
| `GET /api/kpi` | 核心KPI |
| `GET /api/monthly` | 月度温度趋势 |
| `GET /api/zones` | 气候带分布 |
| `GET /api/ranking?category=hottest&limit=10` | 排名(category: hottest/coldest/rainiest/most_extreme) |
| `GET /api/trend` | 趋势(需多年数据) |

## 目录

```
bi_hub/
├── backend/        Flask API (routes/, config.py, db.py)
├── frontend/       Vue3 + ECharts 大屏
├── scripts/        ETL + 数据校验
├── sql/            Hive DDL + MySQL 迁移
├── docs/           实施方案、进度总览、数据字典
└── data/           原始 NOAA CSV (不纳入 git)
```

## 已知限制

- 仅包含 2024 年数据
- NL2SQL 功能待大模型接入
- MapReduce 聚合受 YARN 内存限制，改用 Python 本地聚合

## 数据来源

NOAA Global Summary of the Day (GSOD)
https://www.ncei.noaa.gov/data/global-summary-of-the-day/archive/
