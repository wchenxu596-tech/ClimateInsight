"""MySQL 数据库连接 — 带超时和游标保护"""
import pymysql, pymysql.cursors
from config import MYSQL_HOST, MYSQL_PORT, MYSQL_DATABASE, MYSQL_USER, MYSQL_PASSWORD

_conf = {
    "host": MYSQL_HOST, "port": MYSQL_PORT, "database": MYSQL_DATABASE,
    "user": MYSQL_USER, "password": MYSQL_PASSWORD, "charset": "utf8mb4",
    "connect_timeout": 5, "read_timeout": 30, "write_timeout": 10,
}

def query(sql, params=None):
    conn = pymysql.connect(**_conf)
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()
    finally:
        conn.close()

def query_dict(sql, params=None):
    conn = pymysql.connect(**_conf)
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            cur.execute(sql, params)
            return cur.fetchall()
    finally:
        conn.close()

def health() -> bool:
    try:
        conn = pymysql.connect(**_conf)
        conn.close()
        return True
    except Exception:
        return False
