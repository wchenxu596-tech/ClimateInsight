"""预警规则引擎 — 内置规则 + 可扩展框架

手册 Section 5.2 要求：
- 预置规则：温度高于历史P95、降水低于P20、连续高温≥5天等
- 规则评估生成 alert_event，证据包括计算值、阈值、基线、数据版本
- 预警幂等：相同规则+数据版本+范围不产生重复通知
"""
import hashlib, json
from dataclasses import dataclass, field
from typing import Optional, Any
from datetime import datetime


@dataclass
class AlertRule:
    """预警规则定义"""
    id: str                # 唯一ID
    name: str              # 规则名称
    element: str           # 要素: avg_temperature|total_precip|extreme_days|heat_wave_days
    operator: str          # > | < | >= | <=
    threshold_kind: str    # absolute | percentile | consecutive
    threshold_value: float # 阈值
    severity: str          # red|orange|yellow|blue
    enabled: bool = True
    baseline_years: tuple = (2015, 2020)  # 基线期
    scope: str = "global"  # global|climate_zone|station
    description: str = ""

    def get_dedup_key(self, data_version: str) -> str:
        raw = f"{self.id}|{data_version}|{self.scope}|{self.threshold_value}"
        return hashlib.md5(raw.encode()).hexdigest()[:16]


# ── 预置规则 ──
PRESET_RULES = [
    AlertRule(
        id="alert_temperature_p95",
        name="年均温超过历史P95",
        element="avg_temperature", operator=">",
        threshold_kind="percentile", threshold_value=95,
        severity="red",
        description="当年均温超过基线期（2015-2020）第95百分位时触发"
    ),
    AlertRule(
        id="alert_precip_p20",
        name="年降水低于历史P20",
        element="total_precip", operator="<",
        threshold_kind="percentile", threshold_value=20,
        severity="orange",
        description="当年降水低于基线期第20百分位时触发"
    ),
    AlertRule(
        id="alert_heatwave_consecutive",
        name="连续高温天数≥5",
        element="heat_wave_days", operator=">=",
        threshold_kind="consecutive", threshold_value=5,
        severity="red",
        description="单站连续热浪天数≥5天时触发"
    ),
    AlertRule(
        id="alert_extreme_increase",
        name="极端事件显著增加",
        element="extreme_days", operator=">",
        threshold_kind="percentile", threshold_value=90,
        severity="orange",
        description="当年极端天数超过基线期第90百分位时触发"
    ),
    AlertRule(
        id="alert_coldwave_p90",
        name="寒潮天数异常偏高",
        element="cold_wave_days", operator=">",
        threshold_kind="percentile", threshold_value=90,
        severity="yellow",
        description="当年寒潮天数超过基线期第90百分位时触发"
    ),
]


@dataclass
class AlertEvent:
    rule_id: str
    triggered_at: str     # ISO datetime
    severity: str
    scope: str
    scope_value: str = ""
    evidence: dict = field(default_factory=dict)
    dedup_key: str = ""


class AlertEngine:
    """预警规则引擎"""

    def __init__(self, rules: list[AlertRule] = None):
        self.rules = rules or PRESET_RULES
        self._fired_keys: set = set()  # 幂等去重

    def evaluate(self, value: float, element: str,
                 data_version: str = "v46",
                 baselines: dict = None,
                 scope: str = "global",
                 scope_value: str = "") -> list[AlertEvent]:
        """
        评估单个数据点
        baselines: {p5:..., p20:..., p50:..., p95:..., p99:..., ...}
        """
        events = []
        now = datetime.utcnow().isoformat()

        for rule in self.rules:
            if not rule.enabled or rule.element != element:
                continue

            triggered = False
            evidence = {
                "value": value, "rule_name": rule.name,
                "operator": rule.operator, "threshold_kind": rule.threshold_kind,
                "threshold_value": rule.threshold_value, "severity": rule.severity,
                "data_version": data_version
            }

            if rule.threshold_kind == "absolute":
                if rule.operator == ">" and value > rule.threshold_value:
                    triggered = True
                elif rule.operator == "<" and value < rule.threshold_value:
                    triggered = True
                evidence["threshold"] = rule.threshold_value

            elif rule.threshold_kind == "percentile" and baselines:
                pct_key = f"p{int(rule.threshold_value)}"
                threshold = baselines.get(pct_key)
                if threshold is not None:
                    evidence["threshold"] = threshold
                    evidence["baseline_key"] = pct_key
                    if rule.operator == ">" and value > threshold:
                        triggered = True
                    elif rule.operator == "<" and value < threshold:
                        triggered = True

            if triggered:
                dedup = rule.get_dedup_key(data_version)
                if dedup in self._fired_keys:
                    continue  # 幂等

                self._fired_keys.add(dedup)
                events.append(AlertEvent(
                    rule_id=rule.id,
                    triggered_at=now,
                    severity=rule.severity,
                    scope=scope,
                    scope_value=scope_value,
                    evidence=evidence,
                    dedup_key=dedup
                ))

        return events

    def evaluate_series(self, series: list[dict], element: str,
                        data_version: str = "v46",
                        baselines: dict = None) -> list[AlertEvent]:
        """评估一系列数据点"""
        all_events = []
        for item in series:
            val = item.get("value") or item.get(element)
            if val is None: continue
            scope = item.get("scope", "global")
            scope_val = item.get("scope_value", "")
            events = self.evaluate(val, element, data_version, baselines, scope, scope_val)
            all_events.extend(events)
        return all_events

    def reset(self):
        self._fired_keys.clear()


# ── 全局实例 ──
_engine = AlertEngine()

def evaluate_alerts(value: float, element: str, baselines: dict = None,
                    data_version: str = "v46", scope: str = "global",
                    scope_value: str = "") -> list[dict]:
    """便捷函数：评估并返回 dict 格式事件"""
    events = _engine.evaluate(value, element, data_version, baselines, scope, scope_value)
    return [{
        "rule_id": e.rule_id, "severity": e.severity, "scope": e.scope,
        "scope_value": e.scope_value, "triggered_at": e.triggered_at,
        "evidence": e.evidence
    } for e in events]
