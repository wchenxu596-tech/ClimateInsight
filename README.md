# ClimateInsight — 全球气候智能分析平台

基于 **NOAA GSOD** 全球气象数据的智能分析平台，覆盖 2015–2025 共 11 年数据。支持 KPI 总览、温度趋势、站点排名、气候带演变、极端预警、全球地图和 AI 智能问答。

> 🌐 访问：http://localhost:8080
>
> 📊 数据：NOAA GSOD 全球 ~12,000 气象站，153 万行 DWS，多层级聚合

---

## 🚀 快速启动

```bash
# 1. 克隆
git clone https://github.com/wchenxu596-tech/ClimateInsight.git
cd ClimateInsight

# 2. 配置
cp .env.example .env

# 3. 启动（MySQL + Backend + Frontend）
docker compose up -d

# 4. 导入数据（11 年，需先下载 tar.gz 到 data/raw/）
PYTHONIOENCODING=utf-8 DATA_DIR=f:/ClimateInsight/data \
  python scripts/download_and_load.py --year 2024 --skip-download

# 5. 访问
open http://localhost:8080
```

---

## 🏗️ 系统架构

```
NOAA GSOD tar.gz
  → scripts/download_and_load.py (提取→聚合→MySQL)
    → DWS: dws_station_monthly (153万行, 站×月)
      → ADS: ads_kpi / ads_monthly_trend / ads_ranking / ads_zones / ads_zone_trends / ads_stations
        → Flask API (12 个数据端点 + AI Agent)
          → Vue 3 前端 (ECharts + Element Plus + Grainient 背景)
```

### 技术栈

| 层级 | 技术 |
|---|---|
| 数据源 | NOAA GSOD 2015–2025（11 年 tar.gz） |
| 数据集市 | MySQL 8.0（DWS + 6 张 ADS 预聚合表） |
| 数据管道 | Python（download_and_load.py 一站式） |
| 后端 API | Flask + Gunicorn（REST + 内存缓存 @cached 300s） |
| 前端 | Vue 3 + Vite + ECharts 6 + Element Plus |
| 背景 | @bg-effects/grainient WebGL 动态渐变 |
| 容器化 | Docker Compose（MySQL + Backend + Frontend） |
| AI 引擎 | 规则引擎 + DeepSeek API（双引擎，自动回退） |

---

## 📂 项目结构

```
ClimateInsight/
├── backend/
│   ├── agent/                    # AI 分析助手
│   │   ├── intents.py            # 意图识别（LLM + 规则双引擎）
│   │   ├── prompts.py            # LLM System Prompt
│   │   ├── service.py            # 编排（意图→工具→响应）
│   │   ├── tools.py              # 8 个参数化 SQL 工具
│   │   └── responder.py          # 多段落分析 + 表格 + 图表
│   ├── routes/
│   │   ├── dashboard.py          # KPI / 月度 / 气候带
│   │   ├── rankings.py           # 排名 / 趋势 / 气候带趋势
│   │   ├── alert.py              # 预警 / 地图站点 / 站点详情
│   │   ├── agent.py              # AI 问答入口
│   │   └── health.py             # 健康检查
│   ├── cache.py                  # Flask 内存缓存装饰器
│   ├── app.py                    # 入口
│   ├── config.py                 # 配置
│   ├── db.py                     # MySQL 连接池
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   │   ├── views/
│   │   │   ├── StationMap.vue    # 全球地图（气候带/洲筛选 + 站点弹窗）
│   │   │   ├── Dashboard.vue     # 总览（KPI + 月度 + 排名）
│   │   │   ├── TrendAnalysis.vue # 趋势（5年滑动窗口 + 距平热力图 + 洞察）
│   │   │   ├── CityRanking.vue   # 排名（4类 2×2 网格）
│   │   │   ├── ClimateZones.vue  # 气候带（多图 + 卡片 + 趋势）
│   │   │   ├── AlertDashboard.vue# 预警（风险分级 + 月度事件）
│   │   │   └── StationDetail.vue # 站点详情（月度温度 + 极端事件）
│   │   ├── components/           # 通用组件（GlassCard / ChartPanel / AIPanel 等）
│   │   ├── composables/          # 组合式函数（ECharts 主题 / 站名映射）
│   │   ├── styles/               # tokens.css + base.css（Biophilic 主题）
│   │   └── api/index.js          # API 客户端（前端缓存 + 请求去重）
│   ├── Dockerfile
│   └── nginx.conf
│
├── scripts/
│   ├── download_and_load.py      # 一站式数据导入
│   ├── import_all_years.py       # 批量导入（遍历所有 tar.gz）
│   ├── verify_data.py            # 数据质量校验
│   └── setup.sh                  # 一键部署
│
├── sql/mysql/
│   ├── 001_init.sql
│   ├── 002_create_users.sql
│   └── 003_ads_year_keys.sql
│
├── tests/
│   ├── test_agent_intents.py
│   ├── test_agent_tools.py
│   ├── test_api.py
│   └── test_etl_quality.py
│
├── docker-compose.yml
├── .env.example
├── AI分析助手.md                 # AI 助手完整技术文档
└── README.md
```

---

## 🌐 API 文档

### 数据 API

| 接口 | 方法 | 说明 | 缓存 |
|---|---|---|---|
| `/api/kpi` | GET | KPI 指标（年均温/站点数/极端占比/最高温） | 300s |
| `/api/monthly` | GET | 月度趋势（均温/最高/最低） | 300s |
| `/api/zones` | GET | 气候带分布（5 带站点数） | 300s |
| `/api/ranking` | GET | 站点排名 TOP15（4 类可选） | 300s |
| `/api/trend` | GET | 月度趋势原始数据 | 300s |
| `/api/trend/multi-year` | GET | 多年月度趋势（最多 5 年） | 300s |
| `/api/zones/multi-year` | GET | 多年气候带站点数 | 300s |
| `/api/zones/stats` | GET | 气候带详细统计（温度/降水/极端） | 300s |
| `/api/zones/trend` | GET | 气候带多年趋势（预聚合表，0.01s） | 300s |
| `/api/trend/kpi-history` | GET | 多年 KPI 历史 | 300s |
| `/api/stations` | GET | 全球气象站概要（地图散点，预聚合表 0.09s） | 300s |
| `/api/stations/detail` | GET | 单站月度详情 | 300s |
| `/api/alert/risk` | GET | 极端天气风险评分（四级预警） | 300s |
| `/api/alert/monthly` | GET | 月度极端事件聚合 | 300s |

### AI Agent API

```
POST /api/agent/query
Content-Type: application/json

{
  "question": "这些年变暖了多少？",
  "year": 2025,
  "page": "trend"
}
```

→ 返回 `{ answer, intent, table?, chart? }`

详见 [AI分析助手.md](AI分析助手.md)

---

## 🎨 前端功能

### 页面列表

| 页面 | 功能 | 亮点 |
|---|---|---|
| 🗺️ **地图** | 全球气象站散点图 | 气候带/洲洋筛选、站点弹窗跟随、点击空白关闭 |
| 📊 **总览** | 年度 KPI + 月度趋势 + TOP15 | 红蓝配色区分 |
| 📈 **趋势** | 5 年滑动窗口 + 距平热力图 | KPI 演变卡片 + 四季分组 + 洞察面板 |
| 🏆 **排名** | 最热/最冷/降水/极端 2×2 网格 | 四色独立配色 |
| 🌍 **气候带** | 8:2 多图对比 + 详情卡片 | 预聚合 0.01s 加载 |
| ⚠️ **预警** | 风险评分 + 四级预警 | 红橙黄蓝四级 |
| 🌿 **AI 助手** | 自然语言问答 + 图表渲染 | 17 类意图 + 双引擎 |

### 交互特性

- 玻璃拟态卡片：hover 浮起 + 斜角高光扫过
- 导航脉冲光晕：active 项 3s 呼吸动画
- 按钮按压回弹：`:active scale(0.96)`
- 顶栏实时时钟 + 当地天气（Open-Meteo API）
- Grainient WebGL 动态噪点渐变背景
- AI 面板侧拉：内容等比缩放
- 滚动隔离：`overscroll-behavior: contain`

---

## 📊 数据库

### 表结构

| 表 | 层级 | 行数 | 用途 |
|---|---|---|---|
| `dws_station_monthly` | DWS | 1,530,000 | 站×月明细（21 字段） |
| `ads_kpi` | ADS | 44 | KPI 4 指标 × 11 年 |
| `ads_monthly_trend` | ADS | ~130 | 月度温度 × 11 年 |
| `ads_ranking` | ADS | ~660 | 4 类排名 × TOP15 × 11 年 |
| `ads_zones` | ADS | 55 | 5 气候带站点数 × 11 年 |
| `ads_zone_trends` | ADS | 55 | 气候带温度/降水/极端（预聚合） |
| `ads_stations` | ADS | 133,954 | 站点概要（预聚合，加速地图） |

### 索引

- `PRIMARY KEY (station_id, year, obs_month)` — DWS
- `idx_year_sid (year, station_id)` — 加速站级 GROUP BY
- `idx_climate_zone (year, climate_zone)` — 加速气候带查询
- 所有 ADS 表均含 `PRIMARY KEY (data_year, ...)`

---

## 🧪 测试

```bash
# 意图识别测试
cd backend && python -m pytest ../tests/test_agent_intents.py -v

# Agent 安全测试
cd backend && python -m pytest ../tests/test_agent_tools.py -v

# API 测试（需后端运行）
cd backend && python -m pytest ../tests/test_api.py -v
```

---

## 📖 数据来源

**NOAA Global Summary of the Day (GSOD)**

全球 ~12,000 气象站每日观测数据（温度、降水、气压、风速、极端事件等 28 字段）。

- 官网：https://www.ncei.noaa.gov/data/global-summary-of-the-day/archive/
- 格式：`{year}.tar.gz` → 站级 CSV → 聚合 → MySQL
- 规模：~100MB/年压缩，~370 万条日记录/年

---

## 📄 许可证

MIT License
