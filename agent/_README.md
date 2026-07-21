# AI Agent (已迁移到 backend/agent/)

Agent 实现已整合到 `backend/agent/` 目录:

- `intents.py` — 规则意图识别
- `tools.py` — 白名单工具函数 (参数化SQL)
- `service.py` — 服务编排
- `responder.py` — 响应生成 (模板引擎)

API路由: `backend/routes/agent.py` (`POST /api/agent/query`)

前端页面: `frontend/src/views/BIAgent.vue`
