from __future__ import annotations

import altair as alt
import pandas as pd

from .config import COLORS, SYSTEM_COLORS, SYSTEM_ORDER


def _base_chart_style(chart: alt.Chart, title: str, height: int = 320) -> alt.Chart:
    return (
        chart.properties(height=height, title=title)
        .configure_view(strokeWidth=0)
        .configure_title(anchor="start", color=COLORS["ink"], fontSize=15, fontWeight=800, offset=10)
        .configure_axis(
            labelColor=COLORS["muted"],
            titleColor=COLORS["muted"],
            gridColor="#e8eeeb",
            domainColor="#dfe7e3",
            tickColor="#dfe7e3",
            labelFontSize=11,
            titleFontSize=11,
        )
        .configure_legend(
            titleColor=COLORS["muted"],
            labelColor=COLORS["muted"],
            orient="top",
            labelFontSize=11,
            symbolType="circle",
        )
    )


def system_bar_chart(
    data: pd.DataFrame,
    metric: str,
    title: str,
    x_title: str,
    color: str,
    value_format: str = ",.1f",
) -> alt.Chart:
    chart_data = data.sort_values(metric, ascending=True)
    chart = (
        alt.Chart(chart_data)
        .mark_bar(color=color, cornerRadiusTopRight=8, cornerRadiusBottomRight=8)
        .encode(
            y=alt.Y("system_display:N", sort=chart_data["system_display"].tolist(), title=None),
            x=alt.X(f"{metric}:Q", title=x_title),
            tooltip=[
                alt.Tooltip("system_display:N", title="System"),
                alt.Tooltip(f"{metric}:Q", title=x_title, format=value_format),
            ],
        )
    )
    return _base_chart_style(chart, title, height=288)


def grouped_rate_chart(data: pd.DataFrame, title: str) -> alt.Chart:
    chart_data = data.melt(
        id_vars=["system_display"],
        value_vars=["incident_day_rate_pct", "leak_day_rate_pct"],
        var_name="metric",
        value_name="rate_value",
    )
    label_map = {
        "incident_day_rate_pct": "Operational Incident Day Rate",
        "leak_day_rate_pct": "Leak Day Rate",
    }
    chart_data["metric"] = chart_data["metric"].map(label_map)

    chart = (
        alt.Chart(chart_data)
        .mark_bar(cornerRadiusTopLeft=8, cornerRadiusTopRight=8)
        .encode(
            x=alt.X("system_display:N", sort=SYSTEM_ORDER, title=None, axis=alt.Axis(labelAngle=0)),
            xOffset="metric:N",
            y=alt.Y("rate_value:Q", title="Rate (%)"),
            color=alt.Color(
                "metric:N",
                scale=alt.Scale(
                    domain=["Operational Incident Day Rate", "Leak Day Rate"],
                    range=[COLORS["incident"], COLORS["leak"]],
                ),
                legend=alt.Legend(title=None),
            ),
            tooltip=[
                alt.Tooltip("system_display:N", title="System"),
                alt.Tooltip("metric:N", title="Metric"),
                alt.Tooltip("rate_value:Q", title="Rate", format=",.1f"),
            ],
        )
    )
    return _base_chart_style(chart, title, height=288)


def stacked_cost_chart(data: pd.DataFrame, title: str) -> alt.Chart:
    color_map = {
        "Water": COLORS["water"],
        "Nutrients": COLORS["warning"],
        "Energy": COLORS["muted"],
    }
    chart = (
        alt.Chart(data)
        .mark_bar(cornerRadiusTopLeft=8, cornerRadiusTopRight=8)
        .encode(
            x=alt.X("system_display:N", sort=SYSTEM_ORDER, title=None, axis=alt.Axis(labelAngle=0)),
            y=alt.Y("cost_value:Q", title="Estimated Cost ($)"),
            color=alt.Color(
                "cost_component:N",
                scale=alt.Scale(domain=list(color_map.keys()), range=list(color_map.values())),
                legend=alt.Legend(title=None),
            ),
            tooltip=[
                alt.Tooltip("system_display:N", title="System"),
                alt.Tooltip("cost_component:N", title="Cost component"),
                alt.Tooltip("cost_value:Q", title="Estimated cost", format=",.2f"),
            ],
        )
    )
    return _base_chart_style(chart, title, height=300)


def system_line_chart(
    data: pd.DataFrame,
    metric: str,
    title: str,
    y_title: str,
    value_format: str = ",.1f",
) -> alt.Chart:
    systems = [system for system in SYSTEM_ORDER if system in set(data["system_display"])]
    chart = (
        alt.Chart(data)
        .encode(
            x=alt.X("month:T", title=None, axis=alt.Axis(format="%b %Y", grid=False)),
            y=alt.Y(f"{metric}:Q", title=y_title),
            color=alt.Color(
                "system_display:N",
                scale=alt.Scale(domain=systems, range=[SYSTEM_COLORS[system] for system in systems]),
                legend=alt.Legend(title=None),
            ),
            tooltip=[
                alt.Tooltip("month:T", title="Month"),
                alt.Tooltip("system_display:N", title="System"),
                alt.Tooltip(f"{metric}:Q", title=y_title, format=value_format),
            ],
        )
    )
    layered = chart.mark_line(strokeWidth=3) + chart.mark_circle(size=70)
    return _base_chart_style(layered, title, height=296)


def scatter_tradeoff_chart(
    data: pd.DataFrame,
    x_metric: str,
    y_metric: str,
    title: str,
    x_title: str,
    y_title: str,
    size_metric: str,
    tooltip_metrics: list[tuple[str, str, str]],
) -> alt.Chart:
    systems = [system for system in SYSTEM_ORDER if system in set(data["system_display"])]
    chart_data = data.copy()
    chart_data["system_short"] = chart_data["system_display"].replace(
        {
            "A-shape + Gutters": "A-shape",
            "Conventional": "Conventional",
            "Towers": "Towers",
        }
    )

    base = alt.Chart(chart_data).encode(
        x=alt.X(f"{x_metric}:Q", title=x_title),
        y=alt.Y(f"{y_metric}:Q", title=y_title),
        size=alt.Size(
            f"{size_metric}:Q",
            title=size_metric,
            legend=None,
            scale=alt.Scale(range=[240, 760]),
        ),
        color=alt.Color(
            "system_display:N",
            scale=alt.Scale(domain=systems, range=[SYSTEM_COLORS[system] for system in systems]),
            legend=alt.Legend(title=None),
        ),
        tooltip=[
            alt.Tooltip("system_display:N", title="System"),
            *[
                alt.Tooltip(f"{column}:Q", title=label, format=value_format)
                for column, label, value_format in tooltip_metrics
            ],
        ],
    )

    points = base.mark_circle(opacity=0.88, stroke="white", strokeWidth=1.25)
    labels = (
        alt.Chart(chart_data)
        .mark_text(dy=-12, color=COLORS["ink"], fontSize=11, fontWeight=700)
        .encode(
            x=alt.X(f"{x_metric}:Q"),
            y=alt.Y(f"{y_metric}:Q"),
            text="system_short:N",
        )
    )
    return _base_chart_style(points + labels, title, height=300)


def stacked_severity_chart(data: pd.DataFrame, title: str) -> alt.Chart:
    severity_order = ["Major", "Minor", "Unspecified", "Unknown"]
    chart = (
        alt.Chart(data)
        .mark_bar(cornerRadiusTopLeft=8, cornerRadiusTopRight=8)
        .encode(
            x=alt.X("system_display:N", sort=SYSTEM_ORDER, title=None, axis=alt.Axis(labelAngle=0)),
            y=alt.Y("leak_incidents:Q", title="Leak Incidents"),
            color=alt.Color(
                "leak_severity:N",
                sort=severity_order,
                scale=alt.Scale(
                    domain=severity_order,
                    range=["#b91c1c", "#ef4444", "#fca5a5", "#cbd5e1"],
                ),
                legend=alt.Legend(title=None),
            ),
            tooltip=[
                alt.Tooltip("system_display:N", title="System"),
                alt.Tooltip("leak_severity:N", title="Leak severity"),
                alt.Tooltip("leak_incidents:Q", title="Leak incidents", format=",.0f"),
            ],
        )
    )
    return _base_chart_style(chart, title, height=288)


def score_breakdown_chart(data: pd.DataFrame, title: str) -> alt.Chart:
    chart = (
        alt.Chart(data)
        .mark_bar(cornerRadiusTopLeft=8, cornerRadiusTopRight=8)
        .encode(
            x=alt.X("system_display:N", sort=SYSTEM_ORDER, title=None, axis=alt.Axis(labelAngle=0)),
            y=alt.Y("score_value:Q", title="Normalized Score"),
            color=alt.Color(
                "score_component:N",
                scale=alt.Scale(scheme="tealblues"),
                legend=alt.Legend(title=None),
            ),
            tooltip=[
                alt.Tooltip("system_display:N", title="System"),
                alt.Tooltip("score_component:N", title="Component"),
                alt.Tooltip("score_value:Q", title="Normalized score", format=",.1f"),
            ],
        )
    )
    return _base_chart_style(chart, title, height=300)


def pareto_frontier_chart(
    data: pd.DataFrame,
    x_metric: str,
    y_metric: str,
    title: str,
    x_title: str,
    y_title: str,
) -> alt.Chart:
    chart_data = data.copy()
    systems = [system for system in SYSTEM_ORDER if system in set(chart_data["system_display"])]
    efficient_flags: list[bool] = []

    for _, candidate in chart_data.iterrows():
        dominated = False
        for _, peer in chart_data.iterrows():
            if candidate["system_display"] == peer["system_display"]:
                continue
            if (
                peer[x_metric] <= candidate[x_metric]
                and peer[y_metric] <= candidate[y_metric]
                and (peer[x_metric] < candidate[x_metric] or peer[y_metric] < candidate[y_metric])
            ):
                dominated = True
                break
        efficient_flags.append(not dominated)

    chart_data["frontier_flag"] = ["Pareto-efficient" if flag else "Dominated" for flag in efficient_flags]
    chart_data["system_short"] = chart_data["system_display"].replace({"A-shape + Gutters": "A-shape"})

    base = alt.Chart(chart_data).encode(
        x=alt.X(f"{x_metric}:Q", title=x_title),
        y=alt.Y(f"{y_metric}:Q", title=y_title),
        color=alt.Color(
            "frontier_flag:N",
            scale=alt.Scale(domain=["Pareto-efficient", "Dominated"], range=[COLORS["score"], "#cbd5d1"]),
            legend=alt.Legend(title=None),
        ),
        shape=alt.Shape(
            "system_display:N",
            scale=alt.Scale(domain=systems, range=["circle", "diamond", "square"]),
            legend=None,
        ),
        tooltip=[
            alt.Tooltip("system_display:N", title="System"),
            alt.Tooltip("frontier_flag:N", title="Frontier status"),
            alt.Tooltip(f"{x_metric}:Q", title=x_title, format=",.2f"),
            alt.Tooltip(f"{y_metric}:Q", title=y_title, format=",.2f"),
        ],
    )
    chart = base.mark_point(size=190, filled=True, opacity=0.92)
    labels = (
        alt.Chart(chart_data)
        .mark_text(dy=-13, color=COLORS["ink"], fontSize=11, fontWeight=700)
        .encode(x=alt.X(f"{x_metric}:Q"), y=alt.Y(f"{y_metric}:Q"), text="system_short:N")
    )
    return _base_chart_style(chart + labels, title, height=300)
