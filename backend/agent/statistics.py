"""统计工具 — 纯函数实现，输出含方法/样本量/限制说明

手册 Section 5.1 要求：按独立纯函数实现，输出中写明前提与失败原因。
"""
import math
from typing import Optional


def linear_regression(x: list[float], y: list[float]) -> dict:
    """线性趋势：y = slope * x + intercept"""
    n = len(x)
    if n < 3:
        return {"error": "样本量不足 (需要 ≥3)", "sample_count": n,
                "method": "linear_regression", "unit": "未指定"}

    # 清理 None/NaN
    valid = [(xi, yi) for xi, yi in zip(x, y) if
             xi is not None and yi is not None and math.isfinite(xi) and math.isfinite(yi)]
    if len(valid) < 3:
        return {"error": "有效样本量不足", "sample_count": n, "valid_count": len(valid)}

    xv = [p[0] for p in valid]; yv = [p[1] for p in valid]
    n = len(xv)
    sum_x = sum(xv); sum_y = sum(yv)
    sum_xy = sum(xi*yi for xi,yi in zip(xv,yv))
    sum_x2 = sum(xi*xi for xi in xv)
    sum_y2 = sum(yi*yi for yi in yv)

    slope_num = n * sum_xy - sum_x * sum_y
    slope_den = n * sum_x2 - sum_x * sum_x
    if abs(slope_den) < 1e-10:
        return {"error": "分母为零，无法计算斜率", "sample_count": n}

    slope = slope_num / slope_den
    intercept = (sum_y - slope * sum_x) / n

    # R²
    y_mean = sum_y / n
    ss_res = sum((yi - (slope * xi + intercept))**2 for xi, yi in zip(xv, yv))
    ss_tot = sum((yi - y_mean)**2 for yi in yv)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

    # p-value (简化 t-test)
    if n > 2 and abs(r_squared) < 1:
        se = math.sqrt(ss_res / (n-2) / max(abs(slope_den), 1e-10))
        t_stat = abs(slope) / max(se, 1e-10)
        # Welch-Satterthwaite 近似
        p_value = 2 * (1 - _t_cdf(t_stat, n - 2))
    else:
        t_stat = None; p_value = None

    return {
        "method": "linear_regression",
        "slope": round(slope, 6), "intercept": round(intercept, 4),
        "r_squared": round(r_squared, 4), "r": round(math.sqrt(max(0, r_squared)), 4),
        "p_value": round(p_value, 4) if p_value else None, "t_statistic": round(t_stat, 4) if t_stat else None,
        "sample_count": n, "unit_per_decade": round(slope * 10, 4),
        "limitation": "p值基于t检验近似，小样本时可靠性降低"
    }


def zscore_anomaly(values: list[float], threshold: float = 2.0) -> dict:
    """Z-score 异常检测：|z| > threshold 标记为异常"""
    valid = [v for v in values if v is not None and math.isfinite(v)]
    n = len(valid)
    if n < 4:
        return {"error": "样本量不足", "sample_count": n}

    mean = sum(valid) / n
    variance = sum((v - mean)**2 for v in valid) / n
    std = math.sqrt(variance)
    if std < 1e-10:
        return {"error": "标准差接近零，无变异", "mean": round(mean,4), "std": round(std,4)}

    z_scores = []
    anomalies = []
    for i, v in enumerate(values):
        if v is None or not math.isfinite(v):
            z_scores.append(None)
            continue
        z = (v - mean) / std
        z_scores.append(round(z, 3))
        if abs(z) > threshold:
            anomalies.append({"index": i, "value": round(v,3), "z_score": round(z,3),
                             "direction": "偏高" if z > 0 else "偏低"})

    return {
        "method": "zscore_anomaly",
        "mean": round(mean, 4), "std": round(std, 4),
        "threshold": threshold, "threshold_desc": f"|z| > {threshold}",
        "sample_count": n, "anomaly_count": len(anomalies),
        "anomaly_ratio": round(len(anomalies)/n, 3) if n > 0 else 0,
        "anomalies": anomalies[:20],  # 最多返回20个
        "z_scores": z_scores,
        "limitation": "假设数据近似正态分布；小样本或非正态时结果仅供参考"
    }


def sliding_average(values: list[float], window: int = 5) -> dict:
    """滑动平均"""
    if window < 2: return {"error": "窗口必须 ≥2"}
    n = len(values)
    if n < window: return {"error": f"数据量({n})小于窗口({window})"}

    result = []
    for i in range(n):
        start = max(0, i - window + 1)
        end = i + 1
        window_vals = [v for v in values[start:end] if v is not None and math.isfinite(v)]
        if window_vals:
            result.append(round(sum(window_vals) / len(window_vals), 4))
        else:
            result.append(None)

    return {
        "method": "sliding_average", "window": window,
        "sample_count": n, "smoothed": result,
        "boundary_rule": "起始端使用较小窗口",
        "limitation": "移动平均会平滑掉短时波动，不适用于突变检测"
    }


def descriptive_stats(values: list[float]) -> dict:
    """描述性统计"""
    valid = sorted([v for v in values if v is not None and math.isfinite(v)])
    n = len(valid)
    if n < 1:
        return {"error": "无有效数据"}

    mean = sum(valid) / n
    variance = sum((v - mean)**2 for v in valid) / n
    std = math.sqrt(variance)
    p5_idx = max(0, int(n * 0.05))
    p95_idx = min(n-1, int(n * 0.95))

    return {
        "method": "descriptive_stats",
        "count": n, "mean": round(mean, 4), "std": round(std, 4),
        "min": valid[0], "p5": valid[p5_idx], "median": valid[n//2],
        "p95": valid[p95_idx], "max": valid[-1],
        "range": round(valid[-1] - valid[0], 4),
        "limitation": "百分位数基于简单排序，不适用于加权样本"
    }


# ── 内部辅助 ──
def _t_cdf(t: float, df: int) -> float:
    """简化 Student's t CDF（基于正则化不完备 Beta）"""
    if df <= 0: return 0.5
    x = df / (df + t * t)
    # 简化近似
    return 1 - 0.5 * math.pow(x, df/2) * (1 + (1-x)*(df+2)/4) if 0 < x < 1 else 0.5
