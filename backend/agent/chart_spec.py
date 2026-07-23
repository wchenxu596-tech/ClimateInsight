"""ChartSpec 生成器 — 数据→图表配置的确定性映射

手册 Section 6.2-6.3 要求：
- chart.spec 使用受控的 ECharts Option 子集
- 前端不得执行后端返回的任意脚本
- 规则工具生成，LLM 仅可建议 chart_goal
"""
from typing import Optional

# 色盲友好配色
COLORS = {
    "green":  "#3a674f", "teal":   "#39656b", "orange": "#8b3713",
    "peach":  "#ffdbce", "cyan":   "#bae8ef", "red":    "#ba1a1a",
    "blue":   "#4e79a7", "yellow": "#f28e2b", "purple":"#b07aa1",
    "series": ["#3a674f","#39656b","#8b3713","#4e79a7","#f28e2b","#b07aa1","#59a14f","#e15759"]
}

def chart_spec(chart_goal: str, x: list, y: list, **kwargs) -> Optional[dict]:
    """
    根据 chart_goal 生成受控的 ECharts Option 子集。

    支持的 chart_goal:
    - trend: 折线/面积图
    - compare: 柱状图（多系列）
    - distribution: 柱状图（单系列）
    - proportion: 饼/环形图 (类别≤8)
    - correlation: 散点图
    - table: 文本表格（无图表）
    """
    title = kwargs.get("title", "")
    series_name = kwargs.get("name", "数据")
    labels = kwargs.get("labels", []) or []

    if chart_goal == "trend":
        return {
            "type": "line",
            "title": title,
            "xAxis": {"type": "category", "data": x},
            "yAxis": {"type": "value", "name": series_name},
            "series": [{
                "type": "line", "data": y, "smooth": True,
                "symbolSize": 5,
                "itemStyle": {"color": COLORS["green"]},
                "areaStyle": {"color": {"type":"linear","x":0,"y":0,"x2":0,"y2":1,
                    "colorStops":[{"offset":0,"color":"rgba(58,103,79,0.12)"},
                                  {"offset":1,"color":"rgba(58,103,79,0)"}]}}
            }]
        }

    if chart_goal == "compare":
        series_list = kwargs.get("series_data", {})
        series_config = []
        for i, (sname, sdata) in enumerate(series_list.items()):
            series_config.append({
                "type": "bar", "name": sname, "data": sdata,
                "barMaxWidth": 24, "barGap": "8%",
                "itemStyle": {"color": COLORS["series"][i % len(COLORS["series"])],
                              "borderRadius": [4,4,0,0]}
            })
        return {
            "type": "bar",
            "title": title,
            "xAxis": {"type": "category", "data": x},
            "yAxis": {"type": "value", "name": series_name},
            "series": series_config
        }

    if chart_goal in ("distribution", "histogram"):
        return {
            "type": "bar",
            "title": title,
            "xAxis": {"type": "category", "data": x,
                      "axisLabel": {"rotate": 25, "fontSize": 10}},
            "yAxis": {"type": "value", "name": series_name},
            "series": [{
                "type": "bar", "data": y, "barMaxWidth": 28,
                "itemStyle": {"color": COLORS["teal"], "borderRadius": [4,4,0,0]}
            }]
        }

    if chart_goal == "proportion":
        # 类别 ≤8 适合饼图
        pie_data = [{"name": str(l), "value": v} for l, v in zip(labels, y)] if labels else \
                   [{"name": str(xi), "value": yi} for xi, yi in zip(x, y)]
        return {
            "type": "pie",
            "title": title,
            "series": [{
                "type": "pie", "radius": ["45%", "72%"],
                "center": ["50%", "50%"],
                "label": {"show": False},
                "emphasis": {"label": {"show": True, "fontSize": 16}},
                "data": pie_data,
                "itemStyle": {"borderRadius": 6, "borderColor": "#fff", "borderWidth": 2}
            }]
        }

    if chart_goal == "correlation":
        scatter_data = [[xi, yi] for xi, yi in zip(x, y)]
        return {
            "type": "scatter",
            "title": title,
            "xAxis": {"type": "value", "name": kwargs.get("x_name", "X")},
            "yAxis": {"type": "value", "name": series_name},
            "series": [{
                "type": "scatter", "data": scatter_data, "symbolSize": 8,
                "itemStyle": {"color": COLORS["orange"], "opacity": 0.6}
            }]
        }

    if chart_goal == "table":
        return None  # 仅表格

    # fallback
    return {
        "type": "bar",
        "title": title,
        "xAxis": {"type": "category", "data": x},
        "yAxis": {"type": "value", "name": series_name},
        "series": [{
            "type": "bar", "data": y, "barMaxWidth": 24,
            "itemStyle": {"color": COLORS["green"], "borderRadius": [4,4,0,0]}
        }]
    }
