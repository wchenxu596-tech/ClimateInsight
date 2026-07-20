# ECDW-AI 优化实施方案

---

**版本**：v2.0（基于实际数据优化）  
**日期**：2026-07-20  
**项目周期**：7.21—7.25（5天）

---

## 一、数据实况确认

### 1.1 数据集概况

```
文件: data/UserBehavior.csv
大小: 3.67 GB
行数: 100,150,807 行
字段: user_id, item_id, category_id, behavior_type, timestamp
分隔: 逗号(,)
表头: 无

时间: 2017-11-25 01:21 ~ 2017-12-03 17:38 (9天)
```

### 1.2 行为分布

| 行为 | 原始值 | 数量 | 占比 |
|------|--------|---------|------|
| 浏览 | pv | 89,716,264 | **89.6%** |
| 加购 | cart | 5,530,446 | 5.5% |
| 收藏 | fav | 2,888,258 | 2.9% |
| 购买 | buy | 2,015,839 | 2.0% |

> **关键洞察**：只有 2% 是购买行为（约201万条购买记录），是整个分析的核心。

### 1.3 关键决策：金额字段处理

**问题**：数据集中**没有订单金额字段**，但RFM分析和GMV展示需要。

**推荐方案**：类目价格映射 `category_price_map`
- 每个 `category_id` 映射一个固定单价（如 `category_id % 50 + 10` 得到 10~59 元区间）
- 优点：**结果稳定、可复现、有业务含义**
- 存储为 Hive 维度表 `dim_category_price`，全局复用

---

## 二、架构优化（与初版对比）

### 初版问题

| 问题 | 初版做法 | 优化后 |
|------|----------|--------|
| 表太多 | DWD 3张 + DWS 2张 + ADS 3张 = 8张 | 合并冗余，精简到 **5张核心表** |
| SCD Type 2 | 商品维度用缓慢变化维 | 9天数据不需要，直接用**每日快照** |
| 日期维度表 | 预生成日期维表 | 用 `from_unixtime` 退化到事实表，省掉JOIN |
| 会话计算 | DWS层用窗口函数切分会话 | **1亿行窗口函数→OOM风险**，下沉到Python做(购买用户子集)或跳过 |

### 2.1 精简后的数仓结构（5表）

```
ODS (1表)
  └── ods_user_behavior              ← 原始数据，按dt分区

DWD (1表)                           
  └── dwd_behavior                  ← 清洗+时间退化+金额，唯一定表

DWS (1表)                           
  └── dws_summary_day               ← 用户×日期 汇总，含RFM原始值

ADS (2表)                           
  ├── ads_rfm_segment               ← RFM分层结果
  └── ads_kpi_daily                 ← 每日KPI快照
```

### 2.2 为什么这样精简

**DWD从3张简化为1张的理由**：
- 不需要SCD Type 2：数据只覆盖9天，商品属性（category_id）不会"变化"
- 不需要日期维表：ETL时直接用内置函数生成 `dt`/`hour`/`weekday`，冗余到DWD
- 1张DWD宽表 = 下游所有查询的单一入口，**减少JOIN，加速查询**

**DWS从2张简化为1张的理由**：
- 把RFM的 R/F/M 原始值也放进 DWS 用户日汇总，这样 RFM 直接读 DWS 即可
- 商品热度在 DWD→ADS 用一步SQL搞定，不需要单独的 DWS 商品表

**ADS保持2张**：
- `ads_rfm_segment` 供前端RFM页面和用户分析
- `ads_kpi_daily` 供总览大屏，每行一个KPI，前端直接读

---

## 三、表结构详细设计

### 3.1 ODS 层

```sql
-- 唯一ODS表：与原始数据完全一致
CREATE EXTERNAL TABLE ods_user_behavior (
    user_id       BIGINT   COMMENT '用户ID',
    item_id       BIGINT   COMMENT '商品ID',
    category_id   BIGINT   COMMENT '类目ID',
    behavior_type STRING   COMMENT '行为类型: pv/cart/fav/buy',
    ts            BIGINT   COMMENT 'Unix时间戳(秒)'
)
COMMENT '用户行为原始数据'
PARTITIONED BY (dt STRING COMMENT '日期 yyyy-MM-dd')
ROW FORMAT DELIMITED FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION '/warehouse/ods_user_behavior';
```

**加载方式**：Python脚本预分片 → HDFS → MSCK REPAIR 注册分区

### 3.2 DWD 层

```sql
-- DWD 一张宽表，承载所有明细
CREATE TABLE dwd_behavior (
    -- 主键
    behavior_id   STRING   COMMENT '行为唯一ID: md5(user_id+item_id+ts+behavior_type)',

    -- 原始外键
    user_id       BIGINT,
    item_id       BIGINT,
    category_id   BIGINT,

    -- 标准化行为
    behavior      STRING   COMMENT 'page_view / add_cart / add_fav / purchase',

    -- 时间维度退化（冗余到事实表，减少JOIN）
    ts            BIGINT   COMMENT '原始时间戳',
    dt            STRING   COMMENT '日期 yyyy-MM-dd',
    hour          INT      COMMENT '小时 0-23',
    weekday       INT      COMMENT '周几 1-7',
    is_weekend    INT      COMMENT '是否周末 0/1',

    -- 金额（基于类目价格映射表模拟）
    amount        DECIMAL(10,2) COMMENT '订单金额(仅purchase有值)',

    -- 质量标记
    quality       STRING   COMMENT 'valid / invalid'
)
COMMENT '用户行为明细宽表'
PARTITIONED BY (dt STRING)
STORED AS ORC;
```

**ETL逻辑**：

```sql
INSERT OVERWRITE TABLE dwd_behavior PARTITION(dt='${biz_date}')
SELECT
    md5(concat(user_id, item_id, ts, behavior_type)) AS behavior_id,
    user_id, item_id, category_id,
    CASE behavior_type
        WHEN 'pv'   THEN 'page_view'
        WHEN 'cart' THEN 'add_cart'
        WHEN 'fav'  THEN 'add_fav'
        WHEN 'buy'  THEN 'purchase'
    END AS behavior,
    ts,
    from_unixtime(ts, 'yyyy-MM-dd') AS dt,
    CAST(from_unixtime(ts, 'H') AS INT) AS hour,
    CAST(from_unixtime(ts, 'u') AS INT) AS weekday,
    CASE WHEN CAST(from_unixtime(ts, 'u') AS INT) IN (6,7) THEN 1 ELSE 0 END AS is_weekend,
    CASE WHEN behavior_type = 'buy' THEN cp.price ELSE NULL END AS amount,
    CASE WHEN user_id IS NULL OR item_id IS NULL OR ts IS NULL 
          OR behavior_type NOT IN ('pv','cart','fav','buy')
         THEN 'invalid' ELSE 'valid' END AS quality
FROM ods_user_behavior o
LEFT JOIN dim_category_price cp ON o.category_id = cp.category_id
WHERE o.dt = '${biz_date}';
```

### 3.3 类目价格映射表

```sql
-- 辅助表：基于 category_id 生成固定单价
CREATE TABLE dim_category_price (
    category_id   BIGINT PRIMARY KEY,
    price         DECIMAL(10,2) COMMENT '该类目商品平均单价'
)
STORED AS ORC;

-- 生成逻辑（Python脚本或Hive UDF）：
-- price = (category_id % 50) + 10.0   => 10.0 ~ 59.0 元
```

### 3.4 DWS 层

```sql
-- DWS唯一表：用户×日期，包含RFM原始值
CREATE TABLE dws_summary_day (
    user_id           BIGINT,
    dt                STRING,

    -- 行为统计
    pv_count          BIGINT,
    cart_count        BIGINT,
    fav_count         BIGINT,
    buy_count         BIGINT,

    -- 转化率
    cart_rate         DECIMAL(5,4),
    buy_rate          DECIMAL(5,4),

    -- RFM 原始值（供ADS计算分群）
    last_buy_date     STRING   COMMENT '最近购买日期',
    buy_days          INT      COMMENT '购买天数(F)',
    total_amount      DECIMAL(14,2) COMMENT '累计金额(M)',

    -- 活跃度
    active_hours      INT      COMMENT '活跃小时数(有行为的小时)',
    top_category      BIGINT   COMMENT '最常浏览的类目'
)
COMMENT '用户日汇总宽表'
PARTITIONED BY (dt STRING)
STORED AS ORC;
```

**ETL逻辑**：

```sql
INSERT OVERWRITE TABLE dws_summary_day PARTITION(dt='${biz_date}')
SELECT
    user_id,
    '${biz_date}' AS dt,
    SUM(CASE WHEN behavior='page_view'  THEN 1 ELSE 0 END) AS pv_count,
    SUM(CASE WHEN behavior='add_cart'   THEN 1 ELSE 0 END) AS cart_count,
    SUM(CASE WHEN behavior='add_fav'    THEN 1 ELSE 0 END) AS fav_count,
    SUM(CASE WHEN behavior='purchase'   THEN 1 ELSE 0 END) AS buy_count,
    ROUND(SUM(CASE WHEN behavior='add_cart' THEN 1 END) / NULLIF(SUM(CASE WHEN behavior='page_view' THEN 1 END),0), 4) AS cart_rate,
    ROUND(SUM(CASE WHEN behavior='purchase' THEN 1 END) / NULLIF(SUM(CASE WHEN behavior='page_view' THEN 1 END),0), 4) AS buy_rate,
    MAX(CASE WHEN behavior='purchase' THEN dt END) AS last_buy_date,
    COUNT(DISTINCT CASE WHEN behavior='purchase' THEN dt END) AS buy_days,
    SUM(CASE WHEN behavior='purchase' THEN amount ELSE 0 END) AS total_amount,
    COUNT(DISTINCT hour) AS active_hours,
    FIRST_VALUE(category_id) OVER (PARTITION BY user_id ORDER BY COUNT(*) DESC) AS top_category
FROM dwd_behavior
WHERE dt = '${biz_date}' AND quality = 'valid'
GROUP BY user_id;
```

### 3.5 ADS 层

#### ads_rfm_segment

```sql
CREATE TABLE ads_rfm_segment (
    user_id       BIGINT,
    r_score       INT      COMMENT 'R分 1-5(越大越近)',
    f_score       INT      COMMENT 'F分 1-5(越大越频)',
    m_score       INT      COMMENT 'M分 1-5(越大越多)',
    rfm_label     STRING   COMMENT 'RFM组合 如555',
    segment       STRING   COMMENT '用户分层标签(中文)',
    r_value       INT      COMMENT 'R原始: 距今天数',
    f_value       INT      COMMENT 'F原始: 购买天数',
    m_value       DECIMAL(14,2) COMMENT 'M原始: 累计金额',
    dt            STRING
)
COMMENT 'RFM用户分层(基于整个9天数据)'
PARTITIONED BY (dt STRING)
STORED AS ORC;
```

**RFM计算**：跨9天聚合 → NTILE(5)评分 → CASE WHEN分层。

#### ads_kpi_daily

```sql
CREATE TABLE ads_kpi_daily (
    kpi_name      STRING,
    kpi_value     DECIMAL(18,2),
    prev_value    DECIMAL(18,2)  COMMENT '上一天值(算环比)',
    trend         STRING         COMMENT 'up/down/flat',
    dt            STRING
)
COMMENT '每日KPI快照'
PARTITIONED BY (dt STRING)
STORED AS ORC;
```

**KPI列表**（每行一个指标）：
- `dau` - 日活跃用户数
- `pv_total` - 总浏览量
- `buy_total` - 总购买量
- `gmv` - 总交易额（模拟）
- `buy_rate` - 整体购买转化率
- `cart_rate` - 加购转化率

---

## 四、技术选型调整

| 模块 | 初版 | 优化版 | 理由 |
|------|------|--------|------|
| 数据加载 | LOAD DATA INPATH | Python `hdfs3` 分片上传 | 3.6GB大文件，Python可以按天切分后并行上传 |
| 前端 | Vue3 + Element Plus + ECharts | **同一套** | 成熟方案，不需要改 |
| 后端 | Flask | Flask + `pymysql` + `pyhive` | 加上Hive直连 |
| NL2SQL | LLM Prompt工程 | LLM + **SQL模板兜底** | 保证演示时不会翻车 |
| 报表 | LLM生成全文 | LLM生成洞察 + **固定模板** | 可控性更高，格式稳定 |
| 关联规则 | Apriori全部商品 | **仅TOP类目(前500)** | 400万商品做Apriori→组合爆炸，不可行 |

### 4.1 关于关联规则的重要调整

原始方案中的"购物篮关联规则"有**严重可扩展问题**：

- 400万商品，两两组合 = 8万亿种可能
- 即使用Spark也要跑很久

**实际可行方案**（二选一）：
- **方案A：类目级关联规则**（推荐）  
  只分析 TOP500 类目之间的关联，结果仍然有意义，展示"买了手机壳类目的人42%也会买钢化膜类目"
- **方案B：商品级关联规则（仅高频商品）**  
  只分析购买次数≥100的商品（约几千个），Apriori在Python中秒出

> **建议选方案A**，前端展示效果最好，计算也快。

---

## 五、5天作战计划

### 总览

```
周一    周二     周三     周四     周五
[数仓]  [数仓]   [后端]   [前端]   [集成]
 ████    ████     ████     ████     ██
[环境]  [ETL]    [API]    [大屏]   [答辩]
```

### Day 1（7.21 周一）— 数据就位

| 时段 | 任务 | 负责人 | 产出 |
|------|------|--------|------|
| 上午 | ① Docker环境启动（复用tier4_stu）<br>② 团队对齐会：确认金额方案、分工边界 | A | HDFS/Hive/MySQL 全healthy |
| 上午 | Python数据分片脚本开发：按天切分1亿行→9个CSV | B | `scripts/split_data.py` |
| 下午 | 数据加载：9个分片文件上传HDFS→建ODS外部表→MSCK分区 | B | ODS层完成，行数校验通过 |
| 下午 | 类目价格映射表生成 + DWD建表 | A | `dim_category_price` + `dwd_behavior` DDL |
| 晚上 | DWD ETL脚本，试跑1天数据验证 | A+B | 1天DWD数据走通 |

**当日验收**：ODS 1亿行 = CSV 1亿行；DWD 1天数据能跑通。

### Day 2（7.22 周二）— ETL全线贯通

| 时段 | 任务 | 负责人 | 产出 |
|------|------|--------|------|
| 上午 | DWD 全9天 ETL（批量执行） | A | 9个分区DWD完成 |
| 上午 | 同时：Python RFM计算脚本开发 | B | RFM打分逻辑 |
| 下午 | DWS ETL开发 + 执行 | A | dws_summary_day 9个分区 |
| 下午 | ADS RFM ETL + KPI ETL | B | ads_rfm_segment + ads_kpi_daily |
| 晚上 | 全链路校验：DWD行数 = DWS聚合行数，RFM分群不重不漏 | A+B | 校验通过 |

**当日验收**：四层数仓全部有数据，`SELECT * FROM ads_rfm_segment LIMIT 10` 有结果。

### Day 3（7.23 周三）— 后端API + 前端启动

| 时段 | 任务 | 负责人 | 产出 |
|------|------|--------|------|
| 上午 | Flask项目骨架 + MySQL连接 + Hive连接 | D | `backend/app.py` 基础框架 |
| 上午 | KPI API开发：`/api/kpi?dt=xxx` | D | KPI接口可调通 |
| 下午 | RFM API + 商品热度API + NL2SQL引擎初版 | D | 5个核心API就绪 |
| 下午 | 同时：Vue3项目初始化 + 路由 + 总览页骨架 | C | 前端项目可启动 |
| 晚上 | ECharts集成：KPI卡片 + 折线图 + 饼图 + 柱状图 | C | 总览页图表渲染 |

**当日验收**：`curl localhost:5000/api/kpi` 返回JSON数据；前端总览页面有图表。

### Day 4（7.24 周四）— 全页面补齐 + AI能力

| 时段 | 任务 | 负责人 | 产出 |
|------|------|--------|------|
| 上午 | 前端：用户分析页 + 商品分析页 | C | 3个页面可切换 |
| 上午 | NL2SQL：Prompt调优 + SQL模版兜底 + 安全校验 | D | 10个测试问题通过 |
| 下午 | 前端：关联分析页 + BI问答页 | C | 5个页面全部完成 |
| 下午 | 报表Agent：Prompt + 模板渲染 + HTML输出 | D | 报表可生成 |
| 晚上 | 前后端联调：API数据在前端正确展示 | C+D | 联调通过 |

**当日验收**：5个页面 + NL2SQL + 报表生成 全部可跑通。

### Day 5（7.25 周五）— 集成 + 答辩

| 时段 | 任务 | 负责人 | 产出 |
|------|------|--------|------|
| 上午 | Bug修复 + 数据准确性抽检 | 全员 | 10个随机抽样验证通过 |
| 上午 | API错误处理 + 前端Loading/Empty/Error状态 | C+D | 完善边界情况 |
| 下午 | 答辩PPT + 演示脚本排练 | 全员 | PPT + 演示流程 |
| 下午 | 🎯 答辩 | 全员 | — |

---

## 六、项目的文件清单（交付时应有）

```
bi_hub/
├── README.md                          # 启动指南
├── docs/
│   ├── 需求规格说明书_ECDW-AI.md       # 需求文档
│   └── 实施方案_ECDW-AI.md             # 本文档
├── docker/
│   └── docker-compose.yml              # 基础设施
├── data/
│   └── UserBehavior.csv                # 原始数据
├── sql/
│   ├── 01_dim_price.sql                # 类目价格映射表
│   ├── 02_ods_ddl.sql                  # ODS建表
│   ├── 03_dwd_etl.sql                  # DWD ETL
│   ├── 04_dws_etl.sql                  # DWS ETL
│   ├── 05_ads_rfm.sql                  # ADS RFM
│   ├── 06_ads_kpi.sql                  # ADS KPI
│   └── 07_verify.sql                   # 全链路校验
├── scripts/
│   ├── split_data.py                   # CSV分片
│   ├── load_ods.py                     # 加载到HDFS+Hive
│   └── gen_price_map.py                # 生成价格映射
├── backend/
│   ├── app.py                          # Flask主入口
│   ├── api/
│   │   ├── kpi.py                      # KPI接口
│   │   ├── rfm.py                      # RFM接口
│   │   └── items.py                    # 商品接口
│   ├── nl2sql/
│   │   ├── engine.py                   # NL2SQL引擎
│   │   └── prompts.py                  # Prompt模板
│   ├── agent/
│   │   └── report.py                   # 报表生成
│   └── config.py                       # 数据库配置
├── frontend/
│   ├── src/
│   │   ├── views/
│   │   │   ├── Dashboard.vue           # 总览页
│   │   │   ├── UserAnalysis.vue        # 用户分析页
│   │   │   ├── ProductAnalysis.vue     # 商品分析页
│   │   │   ├── BasketAnalysis.vue      # 关联分析页
│   │   │   └── BIAgent.vue             # BI问答页
│   │   ├── components/                 # 公共图表组件
│   │   ├── api/                        # 接口封装
│   │   └── router/                     # 路由配置
│   └── package.json
└── ppt/                                # 答辩PPT
    └── ECDW-AI答辩.pptx
```

---

## 七、风险管理

| 风险 | 概率 | 影响 | 应对 |
|------|------|------|------|
| Docker环境启不来 | 中 | 高 | 提前验证，准备回退到直接安装 |
| 3.6GB数据加载超时 | 中 | 高 | Python分片上传 + 并行，预计30min内完成 |
| DWD 1亿行ETL OOM | 中 | 中 | 按天分区执行，单次处理~1000万行 |
| 前端时间不够 | 中 | 中 | 第5页(BIAgent)改为简易版，核心4页保底 |
| LLM API 不可用 | 低 | 中 | NL2SQL有SQL模板兜底，报表可用固定模板 |
| Apriori跑不动 | 高 | 低 | 改用类目级关联规则（方案已调整） |

---

## 八、和初版方案的关键差异

| 维度 | 初版 | 优化版 | 理由 |
|------|------|--------|------|
| 表数量 | 8张 | **5张核心表** | 减少不必要的维度表，降低复杂度 |
| DWD | 事实表+2维度表 | **1张宽表** | 9天数据不需要SCD Type2 |
| DWS | 用户表+商品表 | **1张用户表中含商品统计** | 减少聚合层数 |
| 关联规则 | 商品级Apriori | **类目级Apriori** | 400万商品做Apriori不可行 |
| 会话切分 | Hive窗口函数 | **移除** | 1亿行窗口函数OOM，ROI低 |
| 日期维表 | 预生成dim_date | **退化到DWD** | 9天数据不值得单独建维表 |
| 金额 | 未提及方案 | **类目哈希映射** | 给出具体、可复现方案 |

---

> **核心理念**：用最少的表、最简单的SQL完成最多的分析。每个表都有明确的上下游，每条SQL都可以单独验证。5天时间宝贵，不做任何"看起来很美但实际很难落地"的设计。
