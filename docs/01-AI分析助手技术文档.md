# ClimateInsight AI 分析助手 — 完整技术文档

## 一、概述

AI 分析助手是 ClimateInsight 的智能对话模块，位于页面右侧滑出面板。用户通过自然语言提问，系统自动识别意图、查询 NOAA GSOD 全球气候数据库（2015–2025），生成包含文字分析、数据表格和图表的综合回答。

### 系统架构

```
用户输入(自然语言)
    ↓
[前端 AIPanel.vue] → POST /api/agent/query {question, year, page}
    ↓
[Flask routes/agent.py] → 参数校验 + SQL注入防护
    ↓
[agent/service.py] → query(question, year, page)
    ↓
[agent/intents.py] → detect(question)
    ├── LLM 优先: DeepSeek API (temperature=0, 5s timeout)
    └── 规则引擎回退: 关键词匹配 (无网络依赖, 毫秒级)
    ↓
[agent/tools.py] → 参数化SQL查询 ADS/DWS 表
    ↓
[agent/responder.py] → make_response(intent_info, tool_result)
    ↓
返回 JSON: {answer, intent, table?, chart?}
    ↓
[前端 AIPanel.vue] → 渲染文字+表格+ECharts图表
```

---

## 二、意图识别系统

### 2.1 双引擎架构

| 引擎                     | 机制                           | 延迟  | 适用                   |
| ------------------------ | ------------------------------ | ----- | ---------------------- |
| **LLM (DeepSeek)** | System Prompt → JSON 意图分类 | ~1-5s | 复杂/模糊问题          |
| **规则引擎**       | 关键词匹配 + 正则              | <1ms  | 明确问题、LLM 超时回退 |

### 2.2 LLM 配置

```python
# config.py
AGENT_ENABLED = True
LLM_BASE_URL = "https://api.deepseek.com/v1"   # 兼容 OpenAI API
LLM_MODEL = "deepseek-chat"
LLM_API_KEY = "sk-xxx"  # 环境变量
```

LLM 请求参数：`temperature=0`（确定性输出）、`max_tokens=250`、`timeout=5s`。

LLM 失败/超时/格式错误 → 自动回退到规则引擎，不阻断用户请求。

### 2.3 17 类意图完整清单

#### 基础数据查询

| # | 意图`intent`                 | 触发示例                       | LLM JSON                                                      | 规则关键词                        |
| - | ------------------------------ | ------------------------------ | ------------------------------------------------------------- | --------------------------------- |
| 1 | `kpi`                        | "全球平均气温？""气候怎么样？" | `{"intent":"kpi"}`                                          | 全球平均、年均温、KPI、指标、均温 |
| 2 | `monthly`                    | "各月温度变化？""6到9月温度"   | `{"intent":"monthly","months":[6,7,8,9]}`                   | 月度、每月、各月、月均            |
| 3 | `ranking` + `hottest`      | "最热的5个站点？"              | `{"intent":"ranking","category":"hottest","limit":5}`       | 最热、最高温、高温                |
| 4 | `ranking` + `coldest`      | "最冷的地方？"                 | `{"intent":"ranking","category":"coldest","limit":10}`      | 最冷、最低温、最寒                |
| 5 | `ranking` + `rainiest`     | "哪里降水最多？"               | `{"intent":"ranking","category":"rainiest","limit":10}`     | 降水、下雨、雨量                  |
| 6 | `ranking` + `most_extreme` | "极端天气最多的站点？"         | `{"intent":"ranking","category":"most_extreme","limit":10}` | 极端站点、恶劣天气                |
| 7 | `zones`                      | "气候带分布？"                 | `{"intent":"zones"}`                                        | 气候带、热带、温带、寒带          |

#### 趋势与深度分析

| #  | 意图`intent`     | 触发示例               | LLM JSON                                                  | 规则关键词                 |
| -- | ------------------ | ---------------------- | --------------------------------------------------------- | -------------------------- |
| 8  | `trend_analysis` | "这些年变暖了多少？"   | `{"intent":"trend_analysis","years":[2015,2025]}`       | 变暖趋势、这些年、长期趋势 |
| 9  | `seasonal`       | "哪个季节最热？"       | `{"intent":"seasonal"}`                                 | 季节、春夏秋冬、四季       |
| 10 | `zone_detail`    | "哪个气候带升温最快？" | `{"intent":"zone_detail"}`                              | 气候带温度、热带温度变化   |
| 11 | `extremes`       | "极端事件增加了吗？"   | `{"intent":"extremes"}`                                 | 极端事件变化、热浪增加     |
| 12 | `station_query`  | "VOSTOK站的数据？"     | `{"intent":"station_query","station":"VOSTOK"}`         | XX站的数据（正则匹配）     |
| 13 | `compare`        | "2020和2023哪个更热？" | `{"intent":"compare","type":"kpi","years":[2020,2023]}` | 两个年份数字自动触发       |

#### 交互与上下文

| #  | 意图`intent`    | 触发示例               | 说明                                             |
| -- | ----------------- | ---------------------- | ------------------------------------------------ |
| 14 | `page_analysis` | "分析当前页面"         | 拉取 KPI+月度+气候带+趋势+排名**全量数据** |
| 15 | `help`          | "怎么用？""能做什么？" | 返回使用指南                                     |
| 16 | `chat`          | "你好""你是谁？"       | 返回功能介绍                                     |
| 17 | `unknown`       | 无法识别的问题         | 返回提示，引导用户                               |

### 2.4 年份处理策略

```
用户明确提到年份（如"2023年"） → 使用用户年份
用户未提年份 → 使用UI左侧选中的年份（frontend传递）
LLM和规则引擎都未返回年份 → 使用 DATA_YEAR=2025
```

关键技术点：规则引擎默认 `year=None`，让 UI 年份通过 `service.py` 的 `intent_info["year"] = year` 回退填充。

---

## 三、8 个数据工具

所有工具使用**参数化 SQL**（防注入），仅读取 ADS/DWS 聚合表。

| 工具函数                          | 数据源                          | 返回格式                                          | 支持年份 |
| --------------------------------- | ------------------------------- | ------------------------------------------------- | -------- |
| `get_kpi(year)`                 | `ads_kpi` (4行/年)            | `[{kpi_name, kpi_value, kpi_unit, kpi_desc}]`   | 单年     |
| `get_monthly(year)`             | `ads_monthly_trend` (12行/年) | `[{obs_month, avg_temp, avg_max, avg_min}]`     | 单年     |
| `get_ranking(year, cat, limit)` | `ads_ranking`                 | `[{rank_num, station_id, station_name, value}]` | 单年     |
| `get_zones(year)`               | `ads_zones` (5行/年)          | `[{climate_zone, cnt}]`                         | 单年     |
| `get_kpi_history(years)`        | `ads_kpi`                     | `{2015:[...], 2016:[...], ...}`                 | 多年     |
| `get_trend_multi_year(years)`   | `ads_monthly_trend`           | `{2015:[...], ...}`                             | 多年     |
| `get_zones_trend(years)`        | `ads_zone_trends` (55行总计)  | `{year:[{climate_zone,avg_temp,...}]}`          | 多年     |
| `get_station_detail(sid, year)` | `dws_station_monthly`         | `{info:{...}, months:[...]}`                    | 单年     |

### SQL 安全

```python
# routes/agent.py — 拒绝 SQL 关键字
for kw in ["DROP","DELETE","INSERT","UPDATE","TRUNCATE","ALTER","CREATE","SELECT","EXEC","EXECUTE"]:
    if kw in q.upper(): return 400

# tools.py — 仅使用参数化占位符
query_dict("SELECT ... WHERE data_year=%s", (year,))
```

---

## 四、响应生成系统

### 4.1 响应结构

```typescript
{
  code: 0,
  message: "ok",
  data: {
    answer: string,        // 3-8 段结构化文字分析
    intent: string,        // 识别的意图
    table?: {              // 可选：数据表格
      columns: string[],
      rows: string[][]
    },
    chart?: {              // 可选：图表数据
      type: "line"|"bar"|"pie",
      x: string[],
      y: number[],
      name: string
    }
  },
  meta: { data_year: number }
}
```

### 4.2 各意图回答示例

#### KPI（全球KPI指标）

```
📊 2025 年全球气候核心指标
• 极端天气日数占比：5.33%
• 全球年平均温度：14.26°C
• 年度最高气温：56.5°C
• 活跃气象站总数：11618.0个
```

→ 附带表格

#### 趋势分析（trend_analysis）

```
🌡️ 2015–2025 年全球温度趋势分析

📈 总体趋势：2015 年全球年均温 12.8°C，2025 年升至 14.3°C。
累计上升 1.47°C，变暖速率约 1.47°C/十年。

🔍 极值：最暖年份 2025 年（14.3°C），最冷年份 2015 年（12.8°C）。

📊 阶段对比：前半段均温 12.83°C，后半段 14.29°C，后半段偏高 1.47°C。

⚠️ 结论：该时段升温幅度显著，超过自然变率范围。
📋 2025 年极端事件占比：5.33%
```

#### 季节分析（seasonal）

```
🌡️ 四季温度分析（截至 2024 年）

• 春季：2015年 12.3°C → 2024年 13.6°C（升温 1.2°C）
• 夏季：2015年 20.3°C → 2024年 21.1°C（升温 0.9°C）
• 秋季：2015年 13.6°C → 2024年 14.7°C（升温 1.1°C）
• 冬季：2015年 5.1°C → 2024年 6.4°C（升温 1.3°C）

⚠️ 冬季变化最为显著（+1.3°C），冬季变暖可能导致降雪减少、冰川退缩。
```

#### 页面分析（page_analysis）

```
📊 「全球总览」综合分析（2025 年）

📋 核心指标
• 全球年平均温度：14.26°C  ...

📈 多年趋势（2021-2025）
• 2021年 均温 12.8°C → 2025年 均温 14.3°C
累计变化：+1.4°C（2.84°C/十年）

🌡️ 月度温度
年均温 14.3°C，最暖 7月（21.6°C），最冷 1月（5.2°C）

🌍 气候带（共 25301 站）
最大：温带（9534站，38%）...

🔥 气候带温度变化
• 温带：+0.3°C  寒带：+0.2°C  ...

💡 可继续提问：「2020和2024哪个更热？」「极端事件变化趋势？」
```

#### 排名（ranking）

```
🏆 2025 年最高温站点排名 TOP10

榜首为「阿拉法特」，最高温达 45.0°C。
第二名「TURAYNA, QA」42.3°C，与榜首差距 2.7°C。
```

→ 附带条形图 + 表格

---

## 五、前端实现

### 5.1 AIPanel.vue

```vue
<!-- 核心状态 -->
const selectedYear = inject('selectedYear')  // 左侧选中的年份
const activePage = inject('activePage')      // 当前浏览的页面
const messages = ref([...])                   // 对话历史
const loading = ref(false)                    // 加载状态

<!-- 发送消息 -->
async function send() {
  const res = await askAgent(q, selectedYear.value, activePage.value)
  const d = res.data?.data || {}
  const msg = { role: 'assistant', content: d.answer }
  if (d.table) msg.table = d.table
  if (d.chart) msg.chartOption = chartToOption(d.chart)
  messages.value.push(msg)
}
```

### 5.2 动态快捷提问

根据当前页面自动切换快捷提问标签：

| 当前页面 | 快捷提问                                       |
| -------- | ---------------------------------------------- |
| 地图     | "2025年站点分布概况"、"哪个气候带站点最多？"   |
| 总览     | "2025年最热的是哪里？"、"各月温度变化？"       |
| 趋势     | "哪个季节最热？"、"这些年温度上升了多少？"     |
| 排名     | "降水最多的地方？"、"最冷的站点？"             |
| 气候带   | "气候带温度变化趋势？"、"哪个气候带升温最快？" |
| 预警     | "极端事件变化趋势"、"哪个气候带极端事件最多？" |

### 5.3 图表渲染

AI 返回的 `chart` 对象由前端 `chartToOption()` 转换为 ECharts 配置：

```javascript
// 支持三种图表类型
if (c.type === 'bar')  → 柱状图（用于排名、对比）
if (c.type === 'line') → 折线图（用于月度趋势）
if (c.type === 'pie')  → 饼图（用于气候带分布）
```

### 5.4 API 接口

```typescript
POST /api/agent/query
Content-Type: application/json

{
  question: string,   // 用户问题，最长500字符
  year: number,       // 2015-2025，来自左侧年份选择器
  page: string        // 当前页面ID: map|dashboard|trend|ranking|zones|alert
}

// 前端调用
export const askAgent = (question, year = 2024, page = '') =>
  api.post('/agent/query', { question, year, page })
```

---

## 六、数据表依赖

| 表名                    | 行数              | 用途                 | 预聚合   |
| ----------------------- | ----------------- | -------------------- | -------- |
| `ads_kpi`             | 44 (11年×4)      | KPI 指标             | ✅       |
| `ads_monthly_trend`   | ~130 (11年×12月) | 月度温度             | ✅       |
| `ads_ranking`         | ~660              | 各类排名             | ✅       |
| `ads_zones`           | 55 (11年×5带)    | 气候带站点数         | ✅       |
| `ads_zone_trends`     | 55                | 气候带温度/降水/极端 | ✅ 新建  |
| `ads_stations`        | 133,954           | 站点概要(地图)       | ✅ 新建  |
| `dws_station_monthly` | 1,530,000         | 站点月度明细         | 原始 DWS |

---

## 七、安全防护

| 层级           | 措施                                                    |
| -------------- | ------------------------------------------------------- |
| **输入** | 长度限制 500 字符、SQL 关键字黑名单                     |
| **意图** | JSON Schema 校验、多余字段拒绝、category/limit 范围检查 |
| **年份** | 白名单校验`{2015..2025}`                              |
| **SQL**  | 100% 参数化查询，无字符串拼接                           |
| **LLM**  | temperature=0 确定性输出、超时 5s + 规则回退            |

---

## 八、性能

| API               | 冷启动 | 缓存命中 | 优化手段                   |
| ----------------- | ------ | -------- | -------------------------- |
| stations          | 0.09s  | 0.03s    | `ads_stations` 预聚合表  |
| zones/trend       | 0.01s  | 0.004s   | `ads_zone_trends` (55行) |
| trend/multi-year  | 0.02s  | <0.01s   | `ads_monthly_trend` 索引 |
| kpi/monthly/zones | <0.02s | <0.01s   | ADS 小表直读               |

后端缓存：`@cached(300)` — Flask 内存缓存 5 分钟
前端缓存：`cachedGet()` — 30 秒内存 + 并发请求去重

---

## 九、扩展指南

### 添加新意图

1. **prompts.py**: 在 `SYSTEM_PROMPT` 和 `EXPECTED_KEYS` 中添加新意图
2. **intents.py**: 在 `detect_rules()` 中添加关键词匹配规则
3. **service.py**: 在 `query()` 中添加工具调用编排
4. **responder.py**: 添加 `_handle_xxx()` 响应生成函数

### 添加新工具

1. **tools.py**: 添加工具函数 → 注册到 `TOOLS` 字典
2. 优先使用 ADS 预聚合表，避免扫描 DWS 全表

### 年份扩展

1. 更新所有 `VALID_YEARS` / `VALID_YEARS_LIST` 集合
2. 更新 `routes/agent.py` 年份校验范围
3. 运行数据导入脚本填充新年份 ADS 表
