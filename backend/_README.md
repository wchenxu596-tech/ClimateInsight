# Backend - Flask API Server

- `app.py` — 主入口，注册蓝图、静态文件服务
- `config.py` — 集中配置 (环境变量 + dotenv)
- `db.py` — MySQL 连接管理 (pymysql)
- `agent/` — AI分析助手 (意图识别/工具调用/响应生成)
- `routes/` — RESTful API (health/kpi/monthly/zones/ranking/trend/agent)
