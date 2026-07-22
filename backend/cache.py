"""简单的内存缓存 — 对慢查询 API 响应缓存，大幅提升响应速度"""
import time
import hashlib
from functools import wraps
from flask import request, jsonify

_cache = {}

def cached(timeout=300):
    """装饰器：缓存 GET 请求的 JSON 响应，默认超时 300 秒"""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            raw = fn.__name__ + request.full_path
            key = hashlib.md5(raw.encode()).hexdigest()
            now = time.time()
            entry = _cache.get(key)
            if entry and now - entry["ts"] < timeout:
                data, status = entry["data"]
                return jsonify(data), status
            resp = fn(*args, **kwargs)
            # 从 Response 提取数据以便安全缓存
            if hasattr(resp, 'get_json'):
                _cache[key] = {"data": (resp.get_json(), resp.status_code), "ts": now}
            else:
                _cache[key] = {"data": ({}, 200), "ts": now}
            # 定期清理
            if len(_cache) > 200:
                expired = [k for k, v in _cache.items() if now - v["ts"] > timeout * 2]
                for k in expired:
                    del _cache[k]
            return resp
        return wrapper
    return decorator

def invalidate(pattern=None):
    """清除匹配 pattern 的缓存（pattern 为 None 则全部清除）"""
    global _cache
    if pattern is None:
        _cache = {}
    else:
        _cache = {k: v for k, v in _cache.items() if pattern not in k}
