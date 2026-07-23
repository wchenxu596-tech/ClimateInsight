"""集中配置 — 生产环境必须通过环境变量提供"""
from dotenv import load_dotenv
load_dotenv()

import os

MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "climate_dw")
MYSQL_USER = os.getenv("MYSQL_USER", "climate_app")
MYSQL_PASSWORD = os.environ["MYSQL_PASSWORD"]  # 必须提供，无默认值
API_PORT = int(os.getenv("API_PORT", "5000"))
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:8080,http://localhost:5173").split(",")
DATA_YEAR = 2025

HIVE_CONTAINER = os.getenv("HIVE_CONTAINER", "hive-server")
HIVE_JDBC_URL = os.getenv("HIVE_JDBC_URL", "jdbc:hive2://hive-server:10000")

AGENT_ENABLED = os.getenv("AGENT_ENABLED", "true").lower() == "true"
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")
