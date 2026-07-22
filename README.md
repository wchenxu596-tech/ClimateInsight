# ClimateInsight — 全球气候智能分析平台

基于 **NOAA GSOD** 数据的全球气候数据仓库、BI 分析与 AI 智能问答系统。

> 🌐 在线演示：NOAA Global Summary of the Day 全球气象数据可视化平台
>
> 📊 功能：全球 KPI 看板 · 月度温度趋势 · 站点排名 · 气候带分布 · AI 智能问答

---

## 📦 快速部署（克隆即跑）

### 方式一：Docker 自包含部署 ⭐（推荐）

无需任何外部依赖，Docker 一键启动全部服务：

```bash
# 1. 克隆仓库
git clone https://github.com/wchenxu596-tech/ClimateInsight.git
cd ClimateInsight

# 2. 创建环境配置
cp .env.example .env
# （可选）编辑 .env 修改 MySQL 密码等配置

# 3. 启动全部服务（MySQL + 后端 API + 前端页面）
docker compose up -d

# 4. 等待 MySQL 就绪（约 30 秒）
docker compose logs mysql | tail -5
# 看到 "port: 3306  MySQL Community Server" 即就绪

# 5. 加载 NOAA GSOD 气象数据
# 首次运行：从 NOAA 官网下载 2024 年原始数据（约 500MB），解压、聚合后写入 MySQL
# 耗时约 5-10 分钟，取决于网络带宽
docker compose run --rm setup-data --year 2024

# 6. 打开浏览器访问
open http://localhost:8080
```

> 💡 **一键脚本版**：
> ```bash
> bash scripts/setup.sh
> ```

#### 验证部署

```bash
# 查看所有容器状态
docker compose ps

# 检查后端 API 是否正常
curl http://localhost:5000/api/health

# 查看数据是否加载成功
curl http://localhost:5000/api/kpi
```

预期输出：
```json
{"code": 0, "data": [{"kpi_name": "global_avg_temp", ...}]}
```

#### 加载更多年份

```bash
# 加载 2022 年数据
docker compose run --rm setup-data --year 2022

# 加载 2023 年数据
docker compose run --rm setup-data --year 2023
```

---

### 方式二：连接已有 Hadoop 集群部署

适用于已有 Hadoop/Hive + MySQL 集群的环境（如你的 `tier4_stu_*` 容器）。

```bash
# 1. 克隆
git clone https://github.com/wchenxu596-tech/ClimateInsight.git
cd ClimateInsight

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，修改以下配置：
#   MYSQL_HOST=tier4_stu_mysql
#   MYSQL_PORT=3306
#   MYSQL_USER=root
#   MYSQL_PASSWORD=你的密码
#   MYSQL_ROOT_PASSWORD=你的密码

# 3. 使用 Hadoop 覆盖配置启动
# 这会：
#   - 跳过内置 MySQL，使用外部 tier4_stu_mysql
#   - 连接到外部 tier4_hadoop_net 网络
#   - backend 可直接访问 Hive 进行 ETL
docker compose -f docker-compose.yml -f docker-compose.hadoop.yml up -d

# 4. 如果 MySQL 中还没有数据，从 Hive 加载
# （需要 Hive 中已有 ODS/DWD 数据）
docker compose -f docker-compose.yml -f docker-compose.hadoop.yml run --rm data-init --year 2024

# 5. 访问
open http://localhost:8080
```

#### 两种模式对比

| 特性 | 自包含模式 | Hadoop 集群模式 |
|------|-----------|----------------|
| 启动命令 | `docker compose up -d` | `docker compose -f docker-compose.yml -f docker-compose.hadoop.yml up -d` |
| MySQL | 自动创建内置容器 | 连接外部 `tier4_stu_mysql` |
| Hadoop/Hive | 不使用 | 连接外部集群 |
| 数据来源 | NOAA 官网在线下载 | Hive ODS/DWD 表 |
| 适用场景 | 新用户、演示、开发 | 已有大数据基础设施 |

---

### 方式三：本地开发（无 Docker）

```bash
# 前置条件：安装 Python 3.11+、Node.js 20+、MySQL 8.0+

# 1. 初始化 MySQL 数据库和表
mysql -u root -p < sql/mysql/001_init.sql

# 2. 加载数据（从 NOAA 下载 ≈500MB）
pip install pymysql
MYSQL_PASSWORD=你的密码 python scripts/download_and_load.py --year 2024

# 3. 启动后端 API（端口 5000）
cd backend
pip install -r requirements.txt
MYSQL_PASSWORD=你的密码 python app.py

# 4. 启动前端开发服务器（端口 5173）
cd frontend
npm install
npm run dev

# 5. 浏览器访问
open http://localhost:5173
```

---

## 🏗️ 系统架构

### 数据流

```
                        ┌──────────────────────────────────────────────┐
                        │          NOAA GSOD 官网                        │
                        │  (全球 ~12000 个气象站，每日观测，28 个字段)      │
                        └─────────────────────┬────────────────────────┘
                                              │ 下载年度归档 tar.gz
                                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│                      数据处理层                                        │
│                                                                      │
│  方法 A：完整大数据管道（需 Hadoop 集群）                                │
│  ┌──────────┐    ┌──────────┐    ┌────────────────────────────┐     │
│  │ Hive ODS │───▶│ Hive DWD │───▶│ Python ETL (etl_to_mysql)  │     │
│  │ 原始数据  │    │ 清洗转换  │    │ docker exec beeline 读取   │     │
│  │ TEXTFILE  │    │ ORC 格式  │    │ → 内存聚合 → 批量写入      │     │
│  └──────────┘    └──────────┘    └──────────┬─────────────────┘     │
│                                              │                        │
│  方法 B：自包含管道（无需 Hadoop）                                    │
│  ┌────────────────────┐    ┌────────────────────────────┐             │
│  │ download_and_load  │───▶│ 直接解析 NOAA 原始 CSV       │            │
│  │ 下载 → 预处理 → 聚合 │    │ → 内存聚合 → 批量写入      │             │
│  └────────────────────┘    └──────────┬─────────────────┘             │
│                                        │                              │
└────────────────────────────────────────┼──────────────────────────────┘
                                         ▼
┌──────────────────────────────────────────────────────────────────────┐
│                      数据服务层（MySQL）                               │
│                                                                      │
│  ┌─────────────────────┐                                             │
│  │ DWS: 月度汇总        │  dws_station_monthly（站×月聚合，21 列）     │
│  │                     │  ~13.8 万行/年                               │
│  └─────────┬───────────┘                                             │
│            │ SQL 聚合                                                 │
│            ▼                                                         │
│  ┌────────────────────────────────────────────────────────────┐      │
│  │ ADS: 服务表                                                 │      │
│  │  ┌──────────────┐ ┌────────────────┐ ┌──────────────┐     │      │
│  │  │ ads_kpi      │ │ ads_monthly    │ │ ads_ranking  │     │      │
│  │  │ 4 项核心指标  │ │ _trend         │ │ 4 类 TOP15   │     │      │
│  │  │ 年均温/站点数 │ │ 12 个月均温    │ │ 最热/最冷    │     │      │
│  │  │ 极端占比/最高 │ │ 均最高/均最低  │ │ 降水/极端    │     │      │
│  │  └──────────────┘ └────────────────┘ └──────────────┘     │      │
│  │  ┌──────────────┐                                          │      │
│  │  │ ads_zones    │  五带分布（热带/温带/大陆性/寒带/干旱）     │      │
│  │  └──────────────┘                                          │      │
│  └────────────────────────────────────────────────────────────┘      │
└──────────────────────────┬───────────────────────────────────────────┘
                           │ Flask SQL 查询
                           ▼
┌──────────────────────────────────────────────────────────────────────┐
│                     API 服务层（Flask）                                │
│                                                                      │
│  GET /api/kpi       → 核心 KPI 指标                                  │
│  GET /api/monthly   → 月度温度趋势数据                                │
│  GET /api/zones     → 气候带分布数据                                  │
│  GET /api/ranking   → 站点排名数据（支持 hottest/coldest/rainiest/   │
│                        most_extreme 四类）                            │
│  POST /api/agent/query → AI 智能问答                                  │
│                                                                      │
│  AI Agent 流程：                                                     │
│  用户问题 → 意图识别（LLM 优先/规则回退）→ 参数化 SQL 白名单 →        │
│  → 模板响应生成（文本 + 表格 + ECharts 图表）                         │
└──────────────────────┬───────────────────────────────────────────────┘
                       │ JSON
                       ▼
┌──────────────────────────────────────────────────────────────────────┐
│                     前端展示层（Vue 3）                                │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────┐       │
│  │  全局侧边栏（年份选择器）                                    │       │
│  │  2022 │ 2023 │ 2024 ●                                     │       │
│  └──────────────────────────────────────────────────────────┘       │
│                                                                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│  │ 总览      │ │ 趋势      │ │ 排名      │ │ 气候带    │ │ AI 助手  │ │
│  │ Dashboard│ │Trend     │ │Ranking   │ │Zones     │ │BIAgent   │ │
│  │          │ │          │ │          │ │          │ │          │ │
│  │ KPI 卡片 │ │ 月度气温  │ │ 柱状图 + │ │ 饼图 +   │ │ 聊天面板 │ │
│  │ 折线图   │ │ 均温/最高 │ │ 表格     │ │ 列表     │ │ 表格/图表│ │
│  │ 饼图     │ │ /最低    │ │ TOP15   │ │ 五带分布 │ │ 快速查询 │ │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘ │
│                                                                      │
│  技术栈：Vue 3 (Composition API) + Element Plus + ECharts 6 + Vite   │
└──────────────────────────────────────────────────────────────────────┘
```

### 技术栈

| 层级 | 技术 | 用途 |
|------|------|------|
| **数据源** | NOAA GSOD | 全球气象站每日观测数据（28 列原始字段） |
| **数据湖** | Apache Hive (ODS → DWD) | 原始数据存储 + SQL 清洗转换 |
| | Hadoop HDFS | Hive 底层分布式存储 |
| **数据集市** | MySQL 8.0 | DWS 汇总表 + ADS 服务表（5 张） |
| **数据管道** | Python | 聚合 ETL（从 Hive 或直接从 CSV） |
| **后端 API** | Flask + Gunicorn | RESTful API（6 个数据接口 + AI Agent） |
| **前端** | Vue 3 + Vite | Composition API + `<script setup>` |
| **UI 组件** | Element Plus | 表格、按钮、表单、标签 |
| **可视化** | ECharts 6 | 折线图、柱状图、饼图、仪表盘 |
| **容器化** | Docker + Compose | MySQL + Backend + Frontend 三容器编排 |
| **AI 意图识别** | DeepSeek API（可选） | 自然语言 → 结构化 JSON（无 LLM 时纯规则引擎） |

---

## 📂 项目结构

```
ClimateInsight/
├── backend/                      # Flask API 后端
│   ├── agent/                    # AI 分析助手
│   │   ├── intents.py            # 意图识别（LLM + 规则回退）
│   │   ├── prompts.py            # LLM 提示词模板
│   │   ├── service.py            # 服务编排
│   │   ├── tools.py              # 工具白名单（参数化 SQL）
│   │   └── responder.py          # 响应生成器（文本/表格/图表）
│   ├── routes/                   # API 路由
│   │   ├── dashboard.py          # KPI / 月度 / 气候带
│   │   ├── rankings.py           # 站点排名
│   │   ├── agent.py              # AI 问答
│   │   └── health.py             # 健康检查
│   ├── app.py                    # 入口
│   ├── config.py                 # 配置
│   ├── db.py                     # MySQL 连接池
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/                     # Vue 3 前端
│   ├── src/
│   │   ├── views/
│   │   │   ├── Dashboard.vue     # 总览页（KPI + 图表）
│   │   │   ├── TrendAnalysis.vue # 趋势页（月度气温）
│   │   │   ├── CityRanking.vue   # 排名页（TOP15）
│   │   │   ├── ClimateZones.vue  # 气候带页
│   │   │   └── BIAgent.vue       # AI 助手面板
│   │   ├── components/           # 通用组件
│   │   ├── composables/          # 组合式函数
│   │   ├── styles/               # 全局样式（Biophilic 主题）
│   │   └── router/               # 路由配置
│   ├── Dockerfile
│   └── nginx.conf
│
├── scripts/                      # 数据管道
│   ├── download_and_load.py      # 🌟 一键下载 NOAA → 预处理 → 写入 MySQL
│   ├── etl_to_mysql.py           # Hive → MySQL ETL
│   ├── etl_csv_to_mysql.py       # CSV → MySQL ETL（绕过 Hive）
│   ├── preprocess_climate.py     # NOAA 原始 CSV 预处理
│   ├── verify_data.py            # 数据质量校验
│   └── setup.sh                  # 一键部署脚本
│
├── sql/                          # 数据库脚本
│   ├── 01_ods_ddl.sql            # Hive ODS 外部表
│   ├── 02_dwd_etl.sql            # Hive DWD 清洗 ETL
│   └── mysql/
│       ├── 001_init.sql          # MySQL 建库建表
│       ├── 002_create_users.sql  # 创建数据库用户
│       └── 003_ads_year_keys.sql # 多年份主键升级
│
├── tests/                        # 测试
│   ├── test_agent_intents.py     # 意图识别测试
│   ├── test_agent_tools.py       # Agent 安全测试
│   ├── test_api.py               # API 集成测试
│   └── test_etl_quality.py       # 数据质量测试
│
├── docs/                         # 文档
│   ├── 项目架构总览.md
│   ├── API.md
│   ├── 部署运行手册.md
│   └── 数据字典.md
│
├── docker-compose.yml            # 自包含模式（默认）
├── docker-compose.hadoop.yml     # Hadoop 集群模式（覆盖配置）
├── Dockerfile.setup              # 数据加载镜像
├── .env.example                  # 环境变量模板
└── README.md
```

---

## 🌐 API 文档

| 接口 | 方法 | 说明 | 参数 |
|------|------|------|------|
| `/api/health` | GET | 健康检查 | — |
| `/api/kpi` | GET | 核心 KPI（年均温/站点数/极端占比/最高温） | `?year=2024` |
| `/api/monthly` | GET | 月度温度趋势（均温/均最高/均最低） | `?year=2024` |
| `/api/zones` | GET | 气候带分布（热带/温带/大陆性/寒带/干旱） | `?year=2024` |
| `/api/ranking` | GET | 站点排名 TOP15 | `?year=2024&category=hottest` |
| `/api/trend` | GET | 月度趋势数据（原始） | `?year=2024` |
| `POST /api/agent/query` | POST | AI 智能问答 | `{"question": "...", "year": 2024}` |

详见 [API 文档](docs/API.md)

---

## 🧪 测试

```bash
# 意图识别测试（无需数据库）
cd backend && python -m pytest ../tests/test_agent_intents.py -v

# Agent 安全测试
cd backend && python -m pytest ../tests/test_agent_tools.py -v

# API 测试（需后端运行）
cd backend && python -m pytest ../tests/test_api.py -v

# 数据质量测试（需 MySQL 连接）
MYSQL_PASSWORD=xxx cd backend && python -m pytest ../tests/test_etl_quality.py -v
```

---

## ⚠️ 已知限制

| 限制 | 说明 | 计划 |
|------|------|------|
| 数据范围 | 仅含 2024 年数据（多年趋势可导入更多年份） | 已支持 2022-2024 多年份主键 |
| NL2SQL | 占位端点，待大模型接入 | 需配置 DeepSeek API |
| AI Agent | 基于规则识别，不依赖外部 LLM | 可选启用 DeepSeek 增强 |
| MapReduce | Hive MapReduce 聚合受 YARN 内存限制 | 已改用 Python 本地聚合 |
| 实时更新 | 数据一次性导入，不支持 NOAA 实时增量 | 静态分析场景足够 |

---

## 📖 数据来源

**NOAA Global Summary of the Day (GSOD)**

全球气象站每日观测数据，包含超过 12000 个气象站的 28 个观测字段：
温度（均温/最高/最低）、露点、气压（海平面/站点）、能见度、风速（平均/最大/阵风）、降水量、积雪深度、天气现象标记（FRSHTT）等。

- 官网：https://www.ncei.noaa.gov/data/global-summary-of-the-day/archive/
- 格式：每个气象站一个 CSV 文件，按年份归档为 tar.gz
- 数据量：约 500MB/年（压缩），~365 万条日记录/年

---

## 📄 许可证

MIT License
