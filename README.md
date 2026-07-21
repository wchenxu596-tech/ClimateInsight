# ClimateInsight — 全球气候智能分析平台

基于 **NOAA GSOD 2024** 数据的全球气候数据仓库、BI分析与AI智能问答系统。

> ⚠️ **当前数据范围**：仅包含 2024 年数据。多年趋势需导入更多年份后开放。

---

## 架构

```
NOAA GSOD CSV → Hive (ODS → DWD) → Python ETL 聚合 → MySQL (DWS/ADS) → Flask API → Vue3 大屏 + AI Agent
```

---

## 快速启动

### Docker 一键启动 (推荐)

```bash
cp .env.example .env
# 编辑 .env，修改密码
docker compose up -d --build
# 访问 http://localhost:8080
```

### 本地开发

```bash
# 1. 初始化 MySQL
mysql -u root -p < sql/mysql/001_init.sql

# 2. 运行 ETL
$env:MYSQL_PASSWORD='your_password'
python scripts/etl_to_mysql.py --year 2024

# 3. 数据校验
python scripts/verify_data.py --year 2024

# 4. 启动后端
cd backend && pip install -r requirements.txt
$env:MYSQL_PASSWORD='your_password' && python app.py

# 5. 启动前端
cd frontend && npm install && npm run dev
# 访问 http://localhost:5173
```

---

## API

| 接口 | 说明 |
|------|------|
| `GET /api/health` | 健康检查 |
| `GET /api/kpi` | 核心KPI (年均温/站点数/极端占比/最高温) |
| `GET /api/monthly` | 月度温度趋势 |
| `GET /api/zones` | 气候带分布 |
| `GET /api/ranking?category=hottest&limit=10` | 站点排名 (hottest/coldest/rainiest/most_extreme) |
| `GET /api/trend` | 月度趋势（仅2024） |
| `POST /api/agent/query` | AI分析助手 (规则识别+白名单工具) |

详见 [API文档](docs/API.md)

---

## 项目结构

```
bi_hub/
├── backend/            Flask API + Agent
│   ├── agent/          意图识别/工具白名单/响应生成
│   ├── routes/         API路由
│   ├── app.py          入口
│   ├── config.py       配置
│   ├── db.py           MySQL连接
│   └── Dockerfile
├── frontend/           Vue3 + Element Plus + ECharts
│   ├── src/views/      总览/趋势/排名/气候带/AI助手
│   ├── Dockerfile
│   └── nginx.conf
├── scripts/            ETL管道 + 数据校验
│   ├── etl_to_mysql.py Hive→MySQL ETL
│   └── verify_data.py  数据质量校验
├── sql/                DDL/DML
│   ├── 01_ods_ddl.sql  Hive ODS
│   ├── 02_dwd_etl.sql  Hive DWD
│   └── mysql/          MySQL Schema + 升级脚本
├── tests/              测试
├── docs/               文档
│   ├── 部署运行手册.md
│   ├── API.md
│   └── 数据字典.md
└── docker-compose.yml  一键部署
```

---

## 测试

```bash
# Agent意图识别测试 (无需数据库)
cd backend && python -m pytest ../tests/test_agent_intents.py -v

# API测试 (需后端运行)
cd backend && python -m pytest ../tests/test_api.py -v

# ETL质量测试 (需MySQL连接)
$env:MYSQL_PASSWORD='xxx'
cd backend && python -m pytest ../tests/test_etl_quality.py -v
```

---

## 已知限制

- 仅包含 2024 年数据
- NL2SQL 功能待大模型接入（当前为占位端点）
- Agent 基于规则识别，不依赖外部 LLM API
- MapReduce 聚合受 YARN 内存限制，已改用 Python 本地聚合
- Docker 部署不含 Hive（需预先导入数据到 MySQL）

---

## 数据来源

NOAA Global Summary of the Day (GSOD)  
https://www.ncei.noaa.gov/data/global-summary-of-the-day/archive/
