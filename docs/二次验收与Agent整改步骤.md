# ClimateInsight 二次验收与 Agent 整改步骤

> 复核日期：2026-07-20  
> 基线文档：[交付优化实施指南](./交付优化实施指南.md)

## 1. 二次验收结论

当前修改**部分符合预期，但尚未达到可直接交付标准**。已经完成的改动包括：

- `scripts/etl_to_mysql.py` 已没有 Python 语法错误。
- 前端 API 基地址已改为 `VITE_API_BASE_URL || '/api'`，Vite 开发代理已配置。
- 总览页补充了加载、错误、空数据处理。
- AI 页面已诚实标记为“建设中”，没有再伪装成可用的 NL2SQL。
- 新增了 `backend/config.py`、`backend/db.py`、`backend/routes/`、MySQL Schema 和数据校验脚本。
- 历史电商文档已移动到 `docs/archive/`。

但以下核心问题仍阻断交付：

1. **没有 `docker-compose.yml`、Dockerfile 或前端/后端容器配置**，项目不能在新环境一键复现。
2. **后端存在两套实现**：`backend/app.py` 仍使用旧硬编码数据库配置；`config.py`、`db.py`、`routes/` 已创建但未在 `app.py` 注册，实际运行不会使用它们。
3. **ETL、MySQL Schema、API 查询使用的表不一致**：ETL 写 `dws_monthly`，Schema 创建 `dws_station_monthly`；两者字段和主键不同。
4. ETL、校验脚本、后端仍硬编码 `root/123456`、`127.0.0.1` 和 Hive 容器名。
5. 旧 Hive ADS SQL 仍引用不存在的字段（例如 `data_completeness`），不能作为可信交付链路。
6. 前端 Agent 尚未实现；当前仅为占位页，后端 `/api/nl2sql` 同样是占位接口。

后续工作必须按本文顺序进行。不要先实现 Agent；先让数据、服务和接口契约稳定。

---

## 2. 第一优先级：统一后端实现

### 2.1 目标

让 `backend/app.py` 成为唯一入口，并真正使用 `config.py`、`db.py` 与 `routes/` 中的模块。完成后，仓库中不得存在两套并行 API 逻辑。

### 2.2 修改步骤

1. 修改 `backend/app.py`，删除以下旧内容：
   - `DB = {"host":"127.0.0.1", ... "password":"123456"}`；
   - `q()` 函数；
   - 当前在 `app.py` 内定义的 `/api/health`、`/api/kpi`、`/api/monthly`、`/api/zones`、`/api/ranking`、`/api/trend`、`/api/nl2sql` 路由。
2. 从 `config.py` 导入 `CORS_ORIGINS`、`API_PORT`、`FLASK_DEBUG`，从 Flask 配置 CORS：

   ```python
   CORS(app, origins=CORS_ORIGINS)
   ```

3. 导入并注册所有 Blueprint：

   ```python
   from routes.health import bp as health_bp
   from routes.dashboard import bp as dashboard_bp
   from routes.rankings import bp as rankings_bp
   from routes.ai import bp as ai_bp

   app.register_blueprint(health_bp)
   app.register_blueprint(dashboard_bp)
   app.register_blueprint(rankings_bp)
   app.register_blueprint(ai_bp)
   ```

4. 保留 SPA 静态文件 fallback，但只在 `frontend/dist` 存在时返回静态内容；开发模式应允许前端 Vite 独立运行。
5. 在 `config.py` 中取消密码默认值。开发环境也应通过 `.env` 提供，而不是写回代码：

   ```python
   MYSQL_PASSWORD = os.environ["MYSQL_PASSWORD"]
   ```

6. 安装并加载 `python-dotenv`，只在本地开发加载 `.env`；生产环境由 Compose 注入变量。
7. `db.py` 增加连接超时（`connect_timeout`、`read_timeout`、`write_timeout`），并确保游标也被关闭。
8. 所有 API 必须在 SQL 查询中应用 `year`/`data_year` 条件；不能只把请求年份原样返回给 `meta`。

### 2.3 验收

```powershell
cd backend
python -B -c "from app import app; print([str(r) for r in app.url_map.iter_rules()])"
```

验收标准：每条 `/api/*` 路由只出现一次；`app.py` 不含数据库密码；`routes/` 中的路由能出现在 URL map 中。

---

## 3. 第二优先级：统一数据库和 ETL 契约

### 3.1 唯一表名与字段

以 `sql/mysql/001_schema.sql` 为准，把 DWS 表统一命名为：

```text
dws_station_monthly
```

唯一主键为：

```text
(station_id, year, obs_month)
```

API 面向的 ADS 表统一为：

```text
ads_kpi
ads_ranking
ads_monthly_trend
ads_zones
```

每张 ADS 表必须有 `data_year`，且主键/唯一索引能够容纳多个年份。例如：

```sql
-- 示例，不要继续使用仅 obs_month 的主键
PRIMARY KEY (data_year, obs_month)
```

### 3.2 修改 `sql/mysql/001_schema.sql`

1. 不要在常规迁移中使用 `DROP TABLE IF EXISTS`。这会删除已有数据，不适合可重复交付。
2. 将初次建库脚本和升级迁移拆开：

   ```text
   sql/mysql/001_init.sql
   sql/mysql/002_add_year_keys.sql
   sql/mysql/003_indexes.sql
   ```

3. `ads_kpi` 主键改为 `(kpi_name, data_year)`。
4. `ads_ranking` 增加唯一键 `(category, data_year, rank_num)`。
5. `ads_monthly_trend` 主键改为 `(data_year, obs_month)`。
6. `ads_zones` 主键改为 `(data_year, climate_zone)`。

### 3.3 修改 `scripts/etl_to_mysql.py`

按以下顺序改造，不要只改表名：

1. 将 `MYSQL_BASE`、`MYSQL` 替换为从根目录 `.env` 读取的配置。
2. 将 Docker 容器名、Hive JDBC 地址改成环境变量：

   ```dotenv
   HIVE_CONTAINER=hive-server
   HIVE_JDBC_URL=jdbc:hive2://hive-server:10000
   ```

3. DWD 查询必须选择 `year`，聚合键改为：

   ```python
   key = (station_id, year, obs_month)
   ```

4. 删除 `rows = list(reader)`；直接遍历 `reader`，避免将数百万行全部保留在内存。
5. 不能再使用 `TRUNCATE dws_monthly`。应按目标年份删除或使用 Upsert：

   ```sql
   DELETE FROM dws_station_monthly WHERE year = %s;
   ```

   删除动作应在事务、输入校验与临时汇总完成后执行。
6. 向 DWS 写入 `latitude`、`longitude`、`avg_temp_min`、`climate_zone`、`year`，与 Schema 对齐。
7. 统计时不要把解析失败的数据默默变成 `0`、`-999` 或 `999`；应计数并写入拒绝报告。
8. ADS 计算全部增加 `WHERE year=%s` 或 `WHERE data_year=%s`。
9. 排名、月趋势、气候带写入时带上 `data_year`，并使用 `INSERT ... ON DUPLICATE KEY UPDATE`。

### 3.4 修正数据校验

`scripts/verify_data.py` 目前仍假设 ODS 行数大于 9000 万，这与“12,160 个站点 × 2024 年最多 366 天”不一致。

修改为参数化的合理性检查：

```text
最大理论行数 = 站点数 × 当年天数
合理 DWD 行数 = 0 到最大理论行数
```

并增加以下 SQL 检查：

```sql
-- DWS 主键重复
SELECT station_id, year, obs_month, COUNT(*)
FROM dws_station_monthly
GROUP BY station_id, year, obs_month
HAVING COUNT(*) > 1;

-- 指标是否有越界值
SELECT COUNT(*)
FROM dws_station_monthly
WHERE avg_temp NOT BETWEEN -90 AND 60
   OR max_temp NOT BETWEEN -90 AND 60
   OR min_temp NOT BETWEEN -90 AND 60
   OR total_precip < 0;
```

### 3.5 Hive 脚本处理原则

当前 `sql/03_dws_etl.sql` 和 `sql/04_ads_etl.sql` 与 Python ETL 重复且口径不一致。采取以下二选一策略：

- **推荐**：保留 ODS/DWD Hive 脚本，将 `03_dws_etl.sql`、`04_ads_etl.sql` 标注为历史方案，移入 `docs/archive/`；DWS/ADS 仅由 Python 写入 MySQL。
- 若必须保留 Hive DWS/ADS：补齐所有缺失列、修复 `data_completeness`、表名和纬经度字段，并另写 Hive 到 MySQL 的正式同步任务。

禁止在答辩或部署中混用两套方案。

### 3.6 验收

```powershell
python -B -m py_compile scripts\etl_to_mysql.py scripts\verify_data.py
python scripts\etl_to_mysql.py --year 2024
python scripts\verify_data.py --year 2024
```

验收标准：第二次运行不会产生重复记录；查询的年份决定实际数据；DWS、ADS 与 API 的表名完全一致。

---

## 4. 第三优先级：补齐部署与依赖

### 4.1 新增必需文件

必须新增：

```text
docker-compose.yml
backend/Dockerfile
frontend/Dockerfile
frontend/nginx.conf
backend/.dockerignore
frontend/.dockerignore
docs/部署运行手册.md
```

### 4.2 Docker Compose 结构

至少配置：

| 服务 | 职责 | 暴露 |
| --- | --- | --- |
| `mysql` | API 读取的 DWS/ADS 数据库 | 内部 3306；开发时可映射 |
| `backend` | Flask/Gunicorn API | 仅内部 5000 |
| `frontend` | Nginx 静态站点和 `/api` 反向代理 | 对外 8080 |

要求：

1. MySQL 配置命名卷和 healthcheck。
2. 后端使用 `depends_on` 的健康条件，不能仅依赖启动先后顺序。
3. Nginx 将 `/api/` 转发到 `backend:5000`。
4. 用 `.env` 注入密码；`.env.example` 使用 `change-me`，不得继续使用 `123456`。
5. 生产命令使用 Gunicorn 或 Waitress，禁止 `flask run --debug`。
6. Hive 若不能容器化，必须在部署手册列为外部前置条件，并把宿主机命令改成配置变量。

### 4.3 依赖锁定

- 后端 `requirements.txt` 固定版本，例如 `Flask==...`、`PyMySQL==...`、`python-dotenv==...`、`gunicorn==...`。
- 前端保留 `package-lock.json` 并使用 `npm ci`。
- 在 README 说明支持的 Python、Node、Docker 版本。

### 4.4 验收

在没有原开发者本地环境的机器上执行：

```powershell
Copy-Item .env.example .env
docker compose up -d --build
docker compose ps
curl http://localhost:8080/api/health
```

验收：前端能访问，`/api/health` 返回数据库状态；不需要手改源代码中的 IP、端口或容器名。

---

## 5. 第四优先级：完成前端收口

### 5.1 API 参数一致性

当前 `getRanking()` 未向后端传 `year`，而其他接口传了年份。统一 API 客户端：

```javascript
export const getRanking = (year, category = 'hottest', limit = 15) =>
  api.get('/ranking', { params: { year, category, limit } })
```

所有页面从统一的 `selectedYear`（当前仅 2024）读取数据年份；不要在页面和 API 中分别写死 2024。

### 5.2 趋势页修正

目前 `/api/trend` 实际返回月度数据，却使用 `year` 字段名。应二选一：

- 单年版本：返回 `obs_month`，前端标题改为“2024 月度气温变化”，移除“同比变化”柱图。
- 多年版本：增加 `ads_yearly_trend`，返回 `year, avg_temp, temp_change`，前端才展示年度趋势。

在没有 2015–2023 数据之前，推荐第一种。

### 5.3 UI 清理

- 删除未使用的 Vite 默认组件、图标、素材和模板 README。
- 所有数据页都使用与总览相同的 loading/error/empty 状态。
- 在排名图中根据类别显示正确单位：最高/最低温为 `°C`、降水为 `mm`、极端天气为“天”。
- 所有图表显示数据年份和来源说明。

### 5.4 验收

```powershell
cd frontend
npm ci
npm run build
```

验收：构建成功；断开后端时每页均给出可见错误和重试；浏览器控制台无未处理请求错误。

---

## 6. 前端 Agent 功能实现方案

### 6.1 交付定位

第一版 Agent 不应让大模型自由执行 SQL。推荐实现为**受控分析助手**：用户提出问题，后端选择允许的数据工具，工具从已验证的 ADS/DWS 表取数，模型或模板只负责解释结果。

这样可以在不牺牲安全性的前提下实现自然语言交互，也能在没有模型 Key 时降级为固定问答。

### 6.2 功能范围（第一版）

只支持以下问题：

| 意图 | 后端工具 | 返回内容 |
| --- | --- | --- |
| 全球均温/KPI | `get_kpi(year)` | KPI 卡片和一句解释 |
| 月度气温 | `get_monthly(year)` | 12 月数据和趋势描述 |
| 站点排名 | `get_ranking(year, category, limit)` | 排名表和单位 |
| 气候带分布 | `get_zones(year)` | 分布表和占比 |
| 帮助 | `help()` | 支持的问题示例 |

第一版明确不支持：任意 SQL、写入操作、删除操作、跨数据库、超大数据导出、未经验证的多年比较。

### 6.3 后端目录与接口

新增：

```text
backend/
  agent/
    service.py       # 编排入口
    intents.py       # 意图识别和参数抽取
    tools.py         # 白名单数据工具
    responder.py     # 模板/LLM 解释生成
    prompts.py       # 仅在启用 LLM 时使用
  routes/agent.py
```

新增接口：

```text
POST /api/agent/query
```

请求：

```json
{ "question": "2024年最热的10个站点", "year": 2024 }
```

响应：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "answer": "2024 年平均最高温最高的站点如下。",
    "intent": "ranking",
    "tool": "get_ranking",
    "table": {
      "columns": ["排名", "站点", "平均最高温(°C)"],
      "rows": []
    },
    "chart": {
      "type": "bar",
      "x": [],
      "y": []
    },
    "limitations": []
  },
  "meta": { "data_year": 2024 }
}
```

### 6.4 工具白名单实现

在 `agent/tools.py` 中，每个工具是一个独立函数，只能调用参数化 SQL。例如：

```python
def get_ranking(year: int, category: str, limit: int) -> list[dict]:
    if category not in VALID_CATEGORIES:
        raise ValueError("unsupported category")
    limit = min(max(limit, 1), 15)
    return query_dict(
        """SELECT rank_num, station_id, station_name, value
           FROM ads_ranking
           WHERE data_year=%s AND category=%s
           ORDER BY rank_num LIMIT %s""",
        (year, category, limit),
    )
```

约束：

- 工具层不接受 LLM 直接给出的 SQL。
- `year` 仅允许数据库中已有年份；第一版只有 2024。
- `category` 只能来自集合：`hottest/coldest/rainiest/most_extreme`。
- 每次工具调用记录工具名、耗时、结果行数和错误码，不记录密码与完整敏感问题。

### 6.5 意图识别策略

按以下顺序实现：

1. **规则优先**：用关键词和正则识别“最热/最冷/降水/极端天气/月度/气候带/KPI”。这一步不依赖模型，必须先交付。
2. **结构化模型补充（可选）**：如果配置了模型 Key，让模型只输出 JSON：

   ```json
   {"intent":"ranking","category":"hottest","limit":10,"year":2024}
   ```

3. 使用 JSON Schema 校验模型输出；不通过则回退到规则识别或返回“暂不支持”。
4. 绝不将用户问题直接拼接进 SQL。

### 6.6 LLM 接入方式（可选）

新增环境变量，但不将 Key 写入代码或前端：

```dotenv
AGENT_ENABLED=false
LLM_BASE_URL=
LLM_API_KEY=
LLM_MODEL=
```

后端负责调用模型，前端永远不接触 API Key。Prompt 的职责仅限于：

- 解释经过工具验证的结果；
- 标明数据年份和数据限制；
- 不编造数字；
- 数据为空时明确说明；
- 不生成 SQL、不提供数据库操作建议。

未配置 `AGENT_ENABLED=true` 时，`responder.py` 使用模板生成文本，Agent 仍可完成固定问题问答。

### 6.7 前端 `BIAgent.vue` 实施步骤

把当前建设中占位页替换为以下区域：

1. 聊天记录区：仅渲染纯文本，禁止 `v-html`，防止 XSS。
2. 输入框：最大 300 字；Enter 发送；发送时禁用重复请求。
3. 推荐问题按钮：
   - “2024 年全球平均气温是多少？”
   - “最热的 10 个站点？”
   - “各月平均气温如何变化？”
   - “哪个气候带站点最多？”
4. 回答卡片：显示 `answer`、数据年份、限制说明。
5. 结果表格：当响应包含 `table` 时用 `el-table` 渲染。
6. 结果图表：仅当响应包含合法 `chart` 数据时用 ECharts 渲染。
7. 错误和降级：请求失败时提示“分析助手暂不可用，可使用仪表盘查看预置分析”。

API 客户端新增：

```javascript
export const askAgent = (question, year = 2024) =>
  api.post('/agent/query', { question, year })
```

不要继续使用名称为 `nl2sql` 的前端函数，以免误导用户和答辩评委。

### 6.8 Agent 验收用例

| 输入 | 期望 |
| --- | --- |
| “2024年最热的10个站点” | 调用 `get_ranking(hottest, 10)`，返回表格和柱图 |
| “今年气候带分布” | 调用 `get_zones(2024)`，返回分布数据 |
| “删除所有数据” | 不调用任何工具，返回不支持说明 |
| “执行 SELECT * FROM …” | 不执行 SQL，返回不支持说明 |
| 空问题或超长问题 | 返回 400 或前端提示 |
| 未配置模型 Key | 规则和模板模式正常回答预置问题 |

---

## 7. 最终执行顺序

按以下顺序提交和验收，避免返工：

1. 统一后端入口，删除旧硬编码路由，注册 Blueprint。
2. 统一 MySQL 表名、年份主键和 ETL 写入逻辑。
3. 修正数据校验基线与 Hive 历史脚本归档策略。
4. 补齐 Compose、Dockerfile、Nginx 与环境变量。
5. 完成后端/API/ETL 自动化测试。
6. 统一前端年份参数、趋势语义和各页状态。
7. 实现规则优先的受控分析 Agent。
8. 仅在 Agent 稳定后，按开关接入 LLM 做解释增强。
9. 用全新环境运行部署手册，保留测试报告、接口样例和页面截图。

满足以上九步后，项目才能从“局部功能已改造”升级为“可复现、可演示、可交付的 2024 年气候数据 BI 系统”。
