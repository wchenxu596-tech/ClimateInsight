# ClimateInsight API 文档

> 基础URL: `http://localhost:5000/api`  
> 数据范围: 2024 年 NOAA GSOD

---

## 通用响应格式

**成功:**
```json
{"code": 0, "message": "ok", "data": {...}, "meta": {"data_year": 2024}}
```

**错误:**
```json
{"code": 400, "message": "错误描述"}
```

---

## 端点列表

### 1. 健康检查

```
GET /api/health
```

**响应:**
```json
{
  "code": 0,
  "data": {
    "status": "healthy|degraded",
    "database": "connected|disconnected",
    "data_year": 2024
  }
}
```

---

### 2. 核心KPI

```
GET /api/kpi?year=2024
```

**响应 data 字段:**
| kpi_name | kpi_value | kpi_unit | kpi_desc |
|----------|-----------|----------|----------|
| global_avg_temp | 13.96 | °C | 全球年平均温度 |
| total_stations | 12160 | 个 | 活跃气象站总数 |
| extreme_event_pct | 2.5 | % | 极端天气日数占比 |
| hottest_station_temp | 48.2 | °C | 年度最高气温 |

---

### 3. 月度温度趋势

```
GET /api/monthly?year=2024
```

**响应 data 字段:**
| obs_month | avg_temp | avg_max | avg_min |
|-----------|----------|---------|---------|
| 1 | 5.2 | 10.1 | 0.3 |
| ... | ... | ... | ... |
| 12 | 4.8 | 9.6 | 0.1 |

---

### 4. 气候带分布

```
GET /api/zones?year=2024
```

**响应 data 字段:**
| climate_zone | cnt |
|--------------|-----|
| tropical | 2340 |
| temperate | 4520 |
| continental | 3100 |
| polar | 980 |
| arid | 1220 |

---

### 5. 站点排名

```
GET /api/ranking?year=2024&category=hottest&limit=15
```

**参数:**
| 参数 | 类型 | 可选值 | 默认 |
|------|------|--------|------|
| year | int | 2024 | 2024 |
| category | string | hottest, coldest, rainiest, most_extreme | hottest |
| limit | int | 1–50 | 15 |

**响应 data 字段:**
| rank_num | station_id | station_name | value |
|----------|------------|--------------|-------|

---

### 6. 月度趋势（简版）

```
GET /api/trend?year=2024
```

返回月度均温数据，仅含 2024 年。

---

### 7. NL2SQL（占位）

```
POST /api/nl2sql
Content-Type: application/json

{"question": "..."}
```

当前返回占位提示，LLM 功能待接入。

---

### 8. Agent 分析助手

```
POST /api/agent/query
Content-Type: application/json

{"question": "2024年最热的10个站点？", "year": 2024}
```

**参数:**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| question | string | 是 | 自然语言问题，最长300字 |
| year | int | 是 | 数据年份，仅支持2024 |

**响应 data 字段:**
| 字段 | 类型 | 说明 |
|------|------|------|
| answer | string | 自然语言回答 |
| intent | string | 识别的意图类型 |
| table | object | 可选，表格数据 `{columns, rows}` |
| chart | object | 可选，图表定义 `{type, x, y, name}` |
| limitations | array | 数据限制说明 |

**支持的问题类型:**
- 全球KPI查询（年均温、气象站数等）
- 月度温度趋势
- 站点排名（最热/最冷/降水最多/极端天气最多）
- 气候带分布

**安全限制:**
- 不支持SQL语句
- 仅查询ADS表
- 不支持写入/删除操作
