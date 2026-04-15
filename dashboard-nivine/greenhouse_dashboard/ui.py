from __future__ import annotations

from html import escape

import pandas as pd
import streamlit as st

from .analytics import (
    CostModel,
    OutcomeContext,
    build_scenario_comparison,
    build_scenario_summary,
    build_winner_map,
)
from .charts import (
    grouped_rate_chart,
    pareto_frontier_chart,
    score_breakdown_chart,
    scatter_tradeoff_chart,
    stacked_cost_chart,
    stacked_severity_chart,
    system_bar_chart,
    system_line_chart,
)
from .config import (
    COLORS,
    COMPARISON_BASIS_OPTIONS,
    DECISION_MODE_COPY,
    DECISION_MODE_OPTIONS,
    DEFAULT_COST_MODEL,
    EFFICIENCY_SCORE_WEIGHTS,
    OUTCOME_MODE_WEIGHTS,
    OUTCOME_SCORE_WEIGHTS,
    PAGE_META,
    PROXY_MODE_WEIGHTS,
    PROXY_SCORE_WEIGHTS,
    RISK_SCORE_WEIGHTS,
    build_styles,
)
from .data import build_filter_options
from .utils import format_currency, format_date, format_number


def inject_styles() -> None:
    st.markdown(build_styles(), unsafe_allow_html=True)


def render_navigation() -> str:
    with st.sidebar:
        st.markdown(
            """
            <div class="nav-card">
                <div class="nav-kicker">Greenhouse Analytics</div>
                <div class="nav-title">Decision Support</div>
                <div class="nav-copy">
                    Navigate between executive overview, deep comparison, efficiency, risk, planning, and methodology.
                </div>
                <div class="nav-footer">Overview -> Compare -> Optimize -> Prevent -> Simulate -> Explain</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return st.radio(
            "Go to",
            options=list(PAGE_META.keys()),
            format_func=lambda option: PAGE_META[option]["nav_label"],
            label_visibility="collapsed",
        )


def render_controls(df: pd.DataFrame, view_mode: str) -> tuple[dict[str, object], CostModel]:
    options = build_filter_options(df)
    page_icon = PAGE_META[view_mode]["icon"]
    page_context = PAGE_META[view_mode]["context"]
    min_date = df["date_only"].dropna().min()
    max_date = df["date_only"].dropna().max()

    st.markdown(
        f"""
        <div class="toolbar-shell">
            <div class="toolbar-top">
                <div>
                    <div class="toolbar-eyebrow">{page_icon} Analysis Controls</div>
                    <div class="toolbar-title">Scope the current {page_context.lower()} view</div>
                </div>
                <div class="toolbar-copy">
                    Keep the sidebar focused on navigation while filters and assumptions stay in the main workspace.
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    filter_columns = st.columns([1, 1, 1, 1.1], gap="small")
    with filter_columns[0]:
        system_types = st.multiselect(
            "System Type",
            options=options["system_types"],
            default=options["system_types"],
        )
    with filter_columns[1]:
        system_names = st.multiselect(
            "System",
            options=options["system_names"],
            default=options["system_names"],
        )
    with filter_columns[2]:
        crop_types = st.multiselect(
            "Crop Type",
            options=options["crop_types"],
            default=options["crop_types"],
        )
    with filter_columns[3]:
        selected_date_range = st.date_input(
            "Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
        )

    mode_columns = st.columns([1, 1.1, 1.9], gap="small")
    with mode_columns[0]:
        decision_mode = st.selectbox("Decision Mode", DECISION_MODE_OPTIONS, index=0)
    with mode_columns[1]:
        comparison_basis = st.selectbox("Comparison Basis", COMPARISON_BASIS_OPTIONS, index=0)
    with mode_columns[2]:
        st.markdown(
            f"""
            <div class="toolbar-meta">
                <strong>{decision_mode}</strong>: {DECISION_MODE_COPY[decision_mode]}
            </div>
            """,
            unsafe_allow_html=True,
        )

    if isinstance(selected_date_range, (tuple, list)) and len(selected_date_range) == 2:
        start_date, end_date = selected_date_range
    else:
        start_date = end_date = selected_date_range

    st.markdown(
        f"""
        <div class="toolbar-meta">
            <strong>{len(system_names)}</strong> systems, <strong>{len(crop_types)}</strong> crops,
            and a working window from <strong>{format_date(start_date)}</strong> to
            <strong>{format_date(end_date)}</strong>.
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("Advanced cost model assumptions", expanded=False):
        assumption_columns = st.columns(3)
        with assumption_columns[0]:
            water_cost_per_l = st.number_input(
                "Water Cost Per L ($)",
                min_value=0.0,
                value=DEFAULT_COST_MODEL["water_cost_per_l"],
                step=0.0005,
                format="%.4f",
            )
        with assumption_columns[1]:
            nutrient_cost_per_ml = st.number_input(
                "Nutrient Cost Per mL ($)",
                min_value=0.0,
                value=DEFAULT_COST_MODEL["nutrient_cost_per_ml"],
                step=0.0005,
                format="%.4f",
            )
        with assumption_columns[2]:
            energy_cost_per_active_day = st.number_input(
                "Energy Cost Per Active Day ($)",
                min_value=0.0,
                value=DEFAULT_COST_MODEL["energy_cost_per_active_day"],
                step=0.25,
                format="%.2f",
            )
        st.caption(
            "These are adjustable assumptions used to estimate operating cost. The default energy cost is set to zero so it only influences decisions if you choose to model it."
        )

    filters = {
        "view_mode": view_mode,
        "system_types": system_types,
        "system_names": system_names,
        "crop_types": crop_types,
        "start_date": start_date,
        "end_date": end_date,
        "decision_mode": decision_mode,
        "comparison_basis": comparison_basis,
    }
    cost_model = CostModel(
        water_cost_per_l=water_cost_per_l,
        nutrient_cost_per_ml=nutrient_cost_per_ml,
        energy_cost_per_active_day=energy_cost_per_active_day,
    )
    return filters, cost_model


def section_header(title: str, caption: str, eyebrow: str | None = None) -> None:
    if eyebrow:
        st.caption(eyebrow.upper())
    st.subheader(title)
    st.caption(caption)


def _summary_card(card: dict[str, str]) -> str:
    return f"""
    <div class="summary-card">
        <div class="summary-kicker">{escape(card['kicker'])}</div>
        <div class="summary-title">{escape(card['title'])}</div>
        <div class="summary-value">{escape(card['value'])}</div>
        <div class="summary-copy">{escape(card['copy'])}</div>
    </div>
    """


def _mini_summary_card(card: dict[str, str]) -> str:
    return f"""
    <div class="mini-summary-card">
        <div class="mini-summary-kicker">{escape(card['kicker'])}</div>
        <div class="mini-summary-title">{escape(card['title'])}</div>
        <div class="mini-summary-value">{escape(card['value'])}</div>
        <div class="mini-summary-copy">{escape(card['copy'])}</div>
    </div>
    """


def _executive_line(card: dict[str, str]) -> str:
    return (
        '<div class="exec-line">'
        f'<div class="exec-line-label">{escape(card["kicker"])}</div>'
        f'<div class="exec-line-body">{escape(card["title"])} {escape(card["copy"])}</div>'
        "</div>"
    )


def _executive_brief_card(lead_card: dict[str, str], supporting_cards: list[dict[str, str]]) -> str:
    parts = [
        '<div class="exec-brief-shell">',
        f'<div class="exec-brief-kicker">{escape(lead_card["kicker"])}</div>',
        f'<div class="exec-brief-title">{escape(lead_card["title"])}</div>',
        (
            '<div class="exec-brief-copy">'
            f'<strong>{escape(lead_card["value"])}</strong> {escape(lead_card["copy"])}'
            "</div>"
        ),
    ]
    parts.extend(_executive_line(card) for card in supporting_cards)
    parts.append("</div>")
    return "".join(parts)


def _winner_card(label: str, details: dict[str, str]) -> str:
    return f"""
    <div class="decision-card">
        <div class="decision-label">{escape(label)}</div>
        <div class="decision-system">{escape(details['system'])}</div>
        <div class="decision-metric">{escape(details['metric'])}</div>
        <div class="decision-copy">{escape(details['detail'])}</div>
    </div>
    """


def _metric_panel(label: str, value: str, detail: str = "") -> str:
    detail_html = f'<div class="metric-panel-detail">{escape(detail)}</div>' if detail else ""
    return (
        '<div class="metric-panel">'
        f'<div class="metric-panel-label">{escape(label)}</div>'
        f'<div class="metric-panel-value">{escape(value)}</div>'
        f"{detail_html}"
        "</div>"
    )


def render_metric_panels(cards: list[dict[str, str]]) -> None:
    if not cards:
        return
    columns = st.columns(len(cards), gap="small")
    for column, card in zip(columns, cards):
        with column:
            st.markdown(
                _metric_panel(card["label"], card["value"], card.get("detail", "")),
                unsafe_allow_html=True,
            )


def render_note_block(title: str, lines: list[str], style: str = "soft") -> None:
    if not lines:
        return
    body = "".join(f"<div class='note-line'>{escape(line)}</div>" for line in lines if line)
    st.markdown(
        f"""
        <div class="note-shell note-{style}">
            <div class="note-title">{escape(title)}</div>
            {body}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_explainability_table(explainability: pd.DataFrame) -> None:
    if explainability.empty:
        st.info("Score explainability is unavailable for the current selection.")
        return
    display = explainability[
        [
            "system_display",
            "strongest_driver",
            "weakest_driver",
            "top_driver_list",
            "explanation",
        ]
    ].rename(
        columns={
            "system_display": "System",
            "strongest_driver": "Strongest Driver",
            "weakest_driver": "Weakest Driver",
            "top_driver_list": "Top Weighted Drivers",
            "explanation": "Why This System Lands Here",
        }
    )
    st.dataframe(display, use_container_width=True, hide_index=True)


def render_confidence_table(confidence_summary: pd.DataFrame) -> None:
    if confidence_summary.empty:
        st.info("Confidence diagnostics are unavailable for the current selection.")
        return
    display = confidence_summary[
        [
            "system_display",
            "confidence_score",
            "confidence_label",
            "comparability_score",
            "window_coverage_pct",
            "plant_count_coverage_pct",
            "warning_summary",
        ]
    ].rename(
        columns={
            "system_display": "System",
            "confidence_score": "Confidence Score",
            "confidence_label": "Confidence",
            "comparability_score": "Comparability Score",
            "window_coverage_pct": "Window Coverage (%)",
            "plant_count_coverage_pct": "Observed Plant Count Coverage (%)",
            "warning_summary": "Why To Be Careful",
        }
    )
    st.dataframe(
        display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Confidence Score": st.column_config.NumberColumn(format="%.1f"),
            "Comparability Score": st.column_config.NumberColumn(format="%.1f"),
            "Window Coverage (%)": st.column_config.NumberColumn(format="%.1f"),
            "Observed Plant Count Coverage (%)": st.column_config.NumberColumn(format="%.1f"),
        },
    )


def render_rank_table(rank_table: pd.DataFrame, title: str, metric_column: str) -> None:
    if rank_table.empty:
        st.info("Ranking is unavailable for the current selection.")
        return
    display = rank_table[
        [
            "rank",
            "system_display",
            metric_column,
            "estimated_cost_per_100_plants",
            "incident_day_rate_pct",
            "leak_day_rate_pct",
        ]
    ].rename(
        columns={
            "rank": "Rank",
            "system_display": "System",
            metric_column: title,
            "estimated_cost_per_100_plants": "Cost per 100 Plants ($)",
            "incident_day_rate_pct": "Incident Day Rate (%)",
            "leak_day_rate_pct": "Leak Day Rate (%)",
        }
    )
    st.dataframe(
        display,
        use_container_width=True,
        hide_index=True,
        column_config={
            title: st.column_config.NumberColumn(format="%.1f"),
            "Cost per 100 Plants ($)": st.column_config.NumberColumn(format="%.2f"),
            "Incident Day Rate (%)": st.column_config.NumberColumn(format="%.1f"),
            "Leak Day Rate (%)": st.column_config.NumberColumn(format="%.1f"),
        },
    )


def render_compact_rank_table(rank_table: pd.DataFrame, metric_column: str, metric_title: str) -> None:
    if rank_table.empty:
        st.info("Ranking unavailable.")
        return
    display = rank_table[["rank", "system_display", metric_column]].rename(
        columns={"rank": "Rank", "system_display": "System", metric_column: metric_title}
    )
    st.dataframe(
        display,
        use_container_width=True,
        hide_index=True,
        column_config={metric_title: st.column_config.NumberColumn(format="%.1f")},
    )


def render_hero(
    view_mode: str,
    filters: dict[str, object],
    stats: list[tuple[str, str]],
) -> None:
    page = PAGE_META[view_mode]
    scope_summary = f"{len(filters['system_names'])} systems selected"
    crop_summary = f"{len(filters['crop_types'])} crop profiles"
    date_summary = f"{format_date(filters['start_date'])} to {format_date(filters['end_date'])}"
    stat_html = "".join(
        f"""
        <div class="hero-stat">
            <div class="hero-stat-label">{escape(label)}</div>
            <div class="hero-stat-value">{escape(value)}</div>
        </div>
        """
        for label, value in stats
    )
    st.markdown(
        f"""
        <div class="hero-shell">
            <div class="hero-top">
                <div>
                    <div class="hero-eyebrow">{page['icon']} {escape(page['context'])}</div>
                    <div class="hero-title">{escape(page['title'])}</div>
                    <div class="hero-subtitle">{escape(page['subtitle'])}</div>
                </div>
                <div class="hero-meta-card">
                    <div class="hero-meta-label">Current scope</div>
                    <div class="hero-meta-value">{scope_summary}</div>
                    <div class="hero-meta-copy">{crop_summary}<br>{date_summary}</div>
                </div>
            </div>
            <div class="hero-stat-grid">{stat_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_summary_cards(cards: list[dict[str, str]]) -> None:
    if not cards:
        return
    row_size = 3
    for start_index in range(0, len(cards), row_size):
        row_cards = cards[start_index : start_index + row_size]
        columns = st.columns(len(row_cards))
        for column, card in zip(columns, row_cards):
            with column:
                st.markdown(_summary_card(card), unsafe_allow_html=True)


def render_executive_summary(cards: list[dict[str, str]]) -> None:
    if not cards:
        return

    lead_card = cards[0]
    note_card = cards[4] if len(cards) > 4 else None
    cost_card = cards[1] if len(cards) > 1 else None
    supporting_cards = cards[2:4] if len(cards) > 2 else []

    summary_columns = st.columns([1.35, 0.95], gap="medium")
    with summary_columns[0]:
        st.markdown(_executive_brief_card(lead_card, supporting_cards), unsafe_allow_html=True)

    spotlight_cards: list[dict[str, str]] = []
    if cost_card:
        spotlight_cards.append(cost_card)
    if note_card:
        spotlight_cards.append(note_card)

    with summary_columns[1]:
        for card in spotlight_cards:
            st.markdown(_mini_summary_card(card), unsafe_allow_html=True)


def render_winner_cards(winner_map: dict[str, dict[str, str]]) -> None:
    if not winner_map:
        return
    labels = list(winner_map.keys())
    row_size = 3
    for start_index in range(0, len(labels), row_size):
        row_labels = labels[start_index : start_index + row_size]
        columns = st.columns(len(row_labels))
        for column, label in zip(columns, row_labels):
            with column:
                st.markdown(_winner_card(label, winner_map[label]), unsafe_allow_html=True)


def render_recommendations(lines: list[str]) -> None:
    body = "".join(
        f"<div class='recommendation-line'>{escape(line)}</div>" for line in lines if line
    )
    st.markdown(
        f"""
        <div class="recommendation-shell">
            <div class="recommendation-title">Recommendations</div>
            {body}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_methodology_expander(
    outcome_context: OutcomeContext,
    cost_model: CostModel,
    decision_mode: str,
) -> None:
    weights = (
        OUTCOME_MODE_WEIGHTS.get(decision_mode, OUTCOME_SCORE_WEIGHTS)
        if outcome_context.has_yield
        else PROXY_MODE_WEIGHTS.get(decision_mode, PROXY_SCORE_WEIGHTS)
    )
    weight_lines = [
        f"{metric.replace('_', ' ').title()}: {weight * 100:.0f}%"
        for metric, weight in weights.items()
    ]

    with st.expander("📘 Methodology And Assumptions", expanded=False):
        st.markdown(
            f"""
            <div class="methodology-shell">
                <div class="methodology-title">Scoring Methodology</div>
                <div class="methodology-line">{escape(outcome_context.readiness_note)}</div>
                <div class="methodology-line">
                    Operating cost assumptions: water {format_currency(cost_model.water_cost_per_l, 4)} per liter,
                    nutrients {format_currency(cost_model.nutrient_cost_per_ml, 4)} per milliliter,
                    and energy {format_currency(cost_model.energy_cost_per_active_day, 2)} per active day.
                </div>
                <div class="methodology-line">
                    The Overall Performance Score combines normalized metrics so different units can be compared fairly.
                    When yield is missing, the score becomes an operational proxy rather than a true production economics score.
                </div>
                <div class="methodology-title" style="margin-top: 0.9rem;">Current Score Weights</div>
                {''.join(f"<div class='methodology-line'>{escape(line)}</div>" for line in weight_lines)}
                <div class="methodology-title" style="margin-top: 0.9rem;">Supporting Subscores</div>
                <div class="methodology-line">
                    Efficiency Score uses cost, water, and nutrient intensity. Risk Resilience Score uses incident rate,
                    leak rate, and daily water stability.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_data_expander(filtered_df: pd.DataFrame) -> None:
    with st.expander("🗂️ Filtered Data", expanded=False):
        preview_columns = [
            "observation_date",
            "system_display",
            "system_type",
            "crop_types",
            "water_use_l",
            "nutrient_total_ml",
            "issue_flag",
            "leak_flag",
            "leak_severity_label",
            "quality_label",
        ]
        preview = filtered_df[preview_columns].rename(
            columns={
                "observation_date": "Observation Date",
                "system_display": "System",
                "system_type": "System Type",
                "crop_types": "Crop Type",
                "water_use_l": "Water Consumption (L)",
                "nutrient_total_ml": "Nutrient Consumption (mL)",
                "issue_flag": "Operational Incident",
                "leak_flag": "Leak Incident",
                "leak_severity_label": "Leak Severity",
                "quality_label": "Data Quality",
            }
        )
        st.download_button(
            "Download Filtered Data",
            data=preview.to_csv(index=False).encode("utf-8"),
            file_name="greenhouse_decision_support_filtered_data.csv",
            mime="text/csv",
        )
        st.dataframe(preview, use_container_width=True, hide_index=True)


def render_footer_tools(
    filtered_df: pd.DataFrame,
    outcome_context: OutcomeContext,
    cost_model: CostModel,
    decision_mode: str,
) -> None:
    footer_columns = st.columns(2, gap="medium")
    with footer_columns[0]:
        render_methodology_expander(outcome_context, cost_model, decision_mode)
    with footer_columns[1]:
        render_data_expander(filtered_df)


def _render_system_comparison_table(summary: pd.DataFrame, outcome_context: OutcomeContext) -> None:
    comparison = summary.copy().sort_values("overall_performance_score", ascending=False)
    columns = [
        "system_display",
        "system_type",
        "overall_performance_score",
        "efficiency_score",
        "risk_resilience_score",
        "total_estimated_cost",
        "estimated_cost_per_100_plants",
        "water_consumption_l",
        "water_per_100_plants_l",
        "nutrient_consumption_ml",
        "incident_day_rate_pct",
        "leak_day_rate_pct",
        "daily_water_volatility_pct",
        "plant_count_coverage_pct",
    ]
    if outcome_context.has_yield:
        columns[6:6] = ["yield_total", "cost_per_kg", "water_per_kg", "nutrient_per_kg"]

    table = comparison[columns].rename(
        columns={
            "system_display": "System",
            "system_type": "System Type",
            "overall_performance_score": "Overall Performance Score",
            "efficiency_score": "Efficiency Score",
            "risk_resilience_score": "Risk Resilience Score",
            "total_estimated_cost": "Estimated Cost ($)",
            "estimated_cost_per_100_plants": "Estimated Cost per 100 Plants ($)",
            "water_consumption_l": "Water Consumption (L)",
            "water_per_100_plants_l": "Water per 100 Plants (L)",
            "nutrient_consumption_ml": "Nutrient Consumption (mL)",
            "incident_day_rate_pct": "Operational Incident Day Rate (%)",
            "leak_day_rate_pct": "Leak Day Rate (%)",
            "daily_water_volatility_pct": "Water Volatility (%)",
            "plant_count_coverage_pct": "Plant Count Coverage (%)",
            "yield_total": "Yield",
            "cost_per_kg": "Cost per kg",
            "water_per_kg": "Water per kg",
            "nutrient_per_kg": "Nutrients per kg",
        }
    )
    st.dataframe(table, use_container_width=True, hide_index=True)


def _build_tradeoff_decision_table(summary: pd.DataFrame) -> pd.DataFrame:
    lowest_cost_system = summary.loc[
        summary["estimated_cost_per_100_plants"].idxmin(), "system_display"
    ]
    lowest_water_system = summary.loc[
        summary["water_per_100_plants_l"].idxmin(), "system_display"
    ]
    best_efficiency_system = summary.loc[
        summary["efficiency_score"].idxmax(), "system_display"
    ]

    def decision_lens(row: pd.Series) -> str:
        system_name = row["system_display"]
        if system_name == best_efficiency_system:
            return "Best blended efficiency"
        if system_name == lowest_cost_system:
            return "Lowest cost intensity"
        if system_name == lowest_water_system:
            return "Lowest water intensity"
        if row["incident_day_rate_pct"] > summary["incident_day_rate_pct"].median():
            return "Improve reliability before scaling"
        return "Balanced monitor"

    decision_table = summary[
        [
            "system_display",
            "estimated_cost_per_100_plants",
            "water_per_100_plants_l",
            "nutrient_per_100_plants_ml",
            "efficiency_score",
            "incident_day_rate_pct",
        ]
    ].copy()
    decision_table["decision_lens"] = decision_table.apply(decision_lens, axis=1)
    return decision_table.rename(
        columns={
            "system_display": "System",
            "estimated_cost_per_100_plants": "Cost per 100 Plants ($)",
            "water_per_100_plants_l": "Water per 100 Plants (L)",
            "nutrient_per_100_plants_ml": "Nutrients per 100 Plants (mL)",
            "efficiency_score": "Efficiency Score",
            "incident_day_rate_pct": "Operational Incident Day Rate (%)",
            "decision_lens": "Decision Lens",
        }
    )


def render_dashboard_page(
    filtered_df: pd.DataFrame,
    comparison_df: pd.DataFrame,
    comparison_available: bool,
    analysis: dict[str, object],
    filters: dict[str, object],
    outcome_context: OutcomeContext,
    cost_model: CostModel,
    comparison_context: dict[str, object],
) -> None:
    summary = analysis["summary"]
    winner_map = analysis["winner_map"]
    insights = analysis["insights"]
    recommendations = analysis["recommendations"]
    limitations = analysis["limitations"]
    confidence_summary = analysis["confidence_summary"]

    total_cost = summary["total_estimated_cost"].sum()
    total_water = summary["water_consumption_l"].sum()
    total_nutrients = summary["nutrient_consumption_ml"].sum()
    current_incidents = int(filtered_df["issue_flag_bool"].sum())
    current_leaks = int(filtered_df["leak_flag_bool"].sum())
    previous_incidents = int(comparison_df["issue_flag_bool"].sum())
    previous_leaks = int(comparison_df["leak_flag_bool"].sum())

    best_overall = winner_map["Best Overall System"]["system"]
    weakest_system = summary.sort_values("overall_performance_score", ascending=True).iloc[0]["system_display"]
    render_hero(
        "Dashboard",
        filters,
        [
            ("Best Overall System", best_overall),
            ("Decision Mode", filters["decision_mode"]),
            ("Estimated Cost", format_currency(total_cost, 2)),
            ("Watchlist System", weakest_system),
        ],
    )
    render_note_block("Interpretation Note", limitations[:3], style="soft")

    section_header(
        "Executive Summary",
        "A concise readout of the leading system, the largest cost pressure, and the biggest operating risk.",
    )
    render_executive_summary(insights)

    section_header(
        "Management Focus",
        "Current leaders across overall performance, cost, efficiency, and resilience.",
    )
    render_winner_cards(winner_map)

    section_header(
        "Portfolio KPIs",
        "Topline resource consumption and incident levels for the selected operating window.",
    )
    incident_detail = (
        f"vs prior comparison window {current_incidents - previous_incidents:+,}"
        if comparison_available
        else "Current filtered period"
    )
    leak_detail = (
        f"vs prior comparison window {current_leaks - previous_leaks:+,}"
        if comparison_available
        else "Current filtered period"
    )
    render_metric_panels(
        [
            {"label": "Water Consumption", "value": f"{total_water:,.1f} L", "detail": "Across the selected systems and crops"},
            {"label": "Nutrient Consumption", "value": f"{total_nutrients:,.0f} mL", "detail": "Total nutrient input in the current scope"},
            {"label": "Operational Incidents", "value": f"{current_incidents:,}", "detail": incident_detail},
            {"label": "Leak Incidents", "value": f"{current_leaks:,}", "detail": leak_detail},
        ]
    )

    section_header(
        "Decision Visuals",
        "Two high-signal views that show where the strongest system sits and where management should focus next.",
    )
    tradeoff_columns = st.columns(2)
    with tradeoff_columns[0]:
        st.altair_chart(
            system_bar_chart(
                summary,
                metric="overall_performance_score",
                title="Overall Performance Score by system",
                x_title="Overall Performance Score",
                color=COLORS["score"],
                value_format=",.1f",
            ),
            use_container_width=True,
        )

    with tradeoff_columns[1]:
        st.altair_chart(
            pareto_frontier_chart(
                summary,
                x_metric="estimated_cost_per_100_plants",
                y_metric="incident_day_rate_pct",
                title="Cost vs risk frontier",
                x_title="Estimated Cost per 100 Plants ($)",
                y_title="Operational Incident Day Rate (%)",
            ),
            use_container_width=True,
        )

    section_header(
        "Recommended Actions",
        "Short, decision-ready actions based on the current model, fairness setting, and observed weaknesses.",
    )
    render_note_block("Management Actions", recommendations[:4], style="accent")
    if not confidence_summary.empty:
        lowest_conf = confidence_summary.sort_values("confidence_score", ascending=True).iloc[0]
        render_note_block(
            "Confidence Note",
            [
                f"{lowest_conf['system_display']} has the lowest current comparison confidence.",
                lowest_conf["trust_note"],
                comparison_context["basis_note"],
            ],
            style="warning",
        )
    render_footer_tools(filtered_df, outcome_context, cost_model, filters["decision_mode"])


def render_cost_page(
    filtered_df: pd.DataFrame,
    analysis: dict[str, object],
    filters: dict[str, object],
    outcome_context: OutcomeContext,
    cost_model: CostModel,
    comparison_context: dict[str, object],
) -> None:
    summary = analysis["summary"]
    opportunities = analysis["opportunities"]
    cost_composition = analysis["cost_composition"]
    recommendations = analysis["recommendations"]
    confidence_summary = analysis["confidence_summary"]
    rank_tables = analysis["rank_tables"]

    total_cost = summary["total_estimated_cost"].sum()
    top_cost = summary.sort_values("total_estimated_cost", ascending=False).iloc[0]
    lowest_cost = summary.sort_values("estimated_cost_per_100_plants", ascending=True).iloc[0]
    top_savings = opportunities.sort_values("potential_cost_savings", ascending=False).iloc[0]

    render_hero(
        "Cost Optimization",
        filters,
        [
            ("Estimated Portfolio Cost", format_currency(total_cost, 2)),
            ("Largest Cost Driver", top_cost["system_display"]),
            ("Lowest Cost Intensity", lowest_cost["system_display"]),
            ("Visible Savings Opportunity", format_currency(top_savings["potential_cost_savings"], 2)),
        ],
    )
    render_note_block(
        "Cost Interpretation",
        [
            "Estimated costs are assumption-based and should be read as operating proxies rather than audited finance.",
            comparison_context["basis_note"],
        ],
        style="soft",
    )

    section_header(
        "Efficiency And Cost Snapshot",
        "A focused view of spend, resource intensity, and near-term savings opportunity.",
    )
    render_metric_panels(
        [
            {
                "label": "Estimated Cost",
                "value": format_currency(total_cost, 2),
                "detail": "Modeled from water, nutrients, and optional energy assumptions",
            },
            {
                "label": "Water Consumption",
                "value": f"{summary['water_consumption_l'].sum():,.1f} L",
                "detail": f"Highest modeled spend: {top_cost['system_display']}",
            },
            {
                "label": "Nutrient Consumption",
                "value": f"{summary['nutrient_consumption_ml'].sum():,.0f} mL",
                "detail": f"Lowest cost intensity: {lowest_cost['system_display']}",
            },
            {
                "label": "Top Savings Opportunity",
                "value": format_currency(top_savings['potential_cost_savings'], 2),
                "detail": f"Best visible optimization target: {top_savings['system_display']}",
            },
        ]
    )

    chart_columns = st.columns(2)
    with chart_columns[0]:
        st.altair_chart(
            system_bar_chart(
                summary,
                metric="total_estimated_cost",
                title="Estimated cost by system",
                x_title="Estimated Cost ($)",
                color=COLORS["cost"],
                value_format=",.2f",
            ),
            use_container_width=True,
        )

    with chart_columns[1]:
        if cost_composition.empty:
            st.info("Cost composition is unavailable for the current filters.")
        else:
            st.altair_chart(
                stacked_cost_chart(cost_composition, "Estimated cost composition by system"),
                use_container_width=True,
            )

    intensity_columns = st.columns(2)
    with intensity_columns[0]:
        st.altair_chart(
            system_bar_chart(
                summary,
                metric="water_per_100_plants_l",
                title="Water intensity by system",
                x_title="Water per 100 Plants (L)",
                color=COLORS["water"],
                value_format=",.2f",
            ),
            use_container_width=True,
        )

    with intensity_columns[1]:
        st.altair_chart(
            system_bar_chart(
                summary,
                metric="nutrient_per_100_plants_ml",
                title="Nutrient intensity by system",
                x_title="Nutrients per 100 Plants (mL)",
                color=COLORS["warning"],
                value_format=",.1f",
            ),
            use_container_width=True,
        )

    section_header(
        "Optimization Opportunities",
        "Estimated savings reflect the gap between current input intensity and the best peer benchmark in the filtered view.",
    )
    opportunity_table = opportunities[
        [
            "system_display",
            "total_estimated_cost",
            "estimated_cost_per_100_plants",
            "water_per_100_plants_l",
            "nutrient_per_100_plants_ml",
            "potential_water_savings_l",
            "potential_nutrient_savings_ml",
            "potential_cost_savings",
            "priority",
            "opportunity_profile",
        ]
    ].rename(
        columns={
            "system_display": "System",
            "total_estimated_cost": "Estimated Cost ($)",
            "estimated_cost_per_100_plants": "Estimated Cost per 100 Plants ($)",
            "water_per_100_plants_l": "Water per 100 Plants (L)",
            "nutrient_per_100_plants_ml": "Nutrients per 100 Plants (mL)",
            "potential_water_savings_l": "Potential Water Savings (L)",
            "potential_nutrient_savings_ml": "Potential Nutrient Savings (mL)",
            "potential_cost_savings": "Potential Savings ($)",
            "priority": "Priority",
            "opportunity_profile": "Opportunity Profile",
        }
    )
    st.dataframe(opportunity_table, use_container_width=True, hide_index=True)

    section_header(
        "Efficiency Ranking",
        "Cost-focused ranking and decision lenses under the current assumptions.",
    )
    ranking_columns = st.columns([0.95, 1.05], gap="medium")
    with ranking_columns[0]:
        render_compact_rank_table(rank_tables["efficiency"], "efficiency_score", "Efficiency Score")
    with ranking_columns[1]:
        st.dataframe(
            _build_tradeoff_decision_table(summary),
            use_container_width=True,
            hide_index=True,
            column_config={
                "Cost per 100 Plants ($)": st.column_config.NumberColumn(format="%.2f"),
                "Water per 100 Plants (L)": st.column_config.NumberColumn(format="%.2f"),
                "Nutrients per 100 Plants (mL)": st.column_config.NumberColumn(format="%.1f"),
                "Efficiency Score": st.column_config.NumberColumn(format="%.1f"),
                "Operational Incident Day Rate (%)": st.column_config.NumberColumn(format="%.1f%%"),
            },
        )

    section_header(
        "Sensitivity And Trade-Offs",
        "Use this view to see how cost intensity, risk, and comparability interact under the active assumptions.",
    )
    tradeoff_columns = st.columns([1.1, 0.9])
    with tradeoff_columns[0]:
        st.altair_chart(
            scatter_tradeoff_chart(
                summary,
                x_metric="estimated_cost_per_100_plants",
                y_metric="efficiency_score",
                title="Cost intensity vs efficiency score",
                x_title="Estimated Cost per 100 Plants ($)",
                y_title="Efficiency Score",
                size_metric="plant_observations",
                tooltip_metrics=[
                    ("estimated_cost_per_100_plants", "Estimated cost per 100 plants", ",.2f"),
                    ("efficiency_score", "Efficiency Score", ",.1f"),
                    ("water_per_100_plants_l", "Water per 100 plants", ",.2f"),
                ],
            ),
            use_container_width=True,
        )

    with tradeoff_columns[1]:
        st.altair_chart(
            pareto_frontier_chart(
                summary,
                x_metric="estimated_cost_per_100_plants",
                y_metric="water_per_100_plants_l",
                title="Cost vs resource frontier",
                x_title="Estimated Cost per 100 Plants ($)",
                y_title="Water per 100 Plants (L)",
            ),
            use_container_width=True,
        )
        if not confidence_summary.empty:
            lowest_conf = confidence_summary.sort_values("confidence_score", ascending=True).iloc[0]
            render_note_block(
                "Comparability Note",
                [
                    "Not every system is equally rich or equally aligned in the data.",
                    lowest_conf["trust_note"],
                ],
                style="warning",
            )

    render_recommendations(recommendations[:4])
    render_footer_tools(filtered_df, outcome_context, cost_model, filters["decision_mode"])


def render_problem_page(
    filtered_df: pd.DataFrame,
    analysis: dict[str, object],
    filters: dict[str, object],
    outcome_context: OutcomeContext,
    cost_model: CostModel,
    comparison_context: dict[str, object],
) -> None:
    summary = analysis["summary"]
    alerts = analysis["alerts"]
    monthly_trends = analysis["monthly_trends"]
    leak_severity = analysis["leak_severity"]
    recommendations = analysis["recommendations"]
    issue_patterns = analysis["issue_patterns"]
    rank_tables = analysis["rank_tables"]

    highest_incident = summary.sort_values("incident_day_rate_pct", ascending=False).iloc[0]
    highest_leak = summary.sort_values("leak_day_rate_pct", ascending=False).iloc[0]
    most_stable = summary.sort_values("daily_water_volatility_pct", ascending=True).iloc[0]
    alert_count = len(alerts)

    render_hero(
        "Problem Detection",
        filters,
        [
            ("Highest Incident Exposure", highest_incident["system_display"]),
            ("Highest Leak Exposure", highest_leak["system_display"]),
            ("Open Alerts", f"{alert_count:,}"),
            ("Most Stable System", most_stable["system_display"]),
        ],
    )
    render_note_block(
        "Monitoring Note",
        [
            "These alerts are rule-based early warnings designed to support fast operational review.",
            comparison_context["basis_note"],
        ],
        style="soft",
    )

    section_header(
        "Risk Snapshot",
        "Where reliability issues are concentrated today and which systems need faster intervention.",
    )
    render_metric_panels(
        [
            {
                "label": "Operational Incidents",
                "value": f"{int(filtered_df['issue_flag_bool'].sum()):,}",
                "detail": "All flagged incidents in the current view",
            },
            {
                "label": "Leak Incidents",
                "value": f"{int(filtered_df['leak_flag_bool'].sum()):,}",
                "detail": "Leak-related incidents requiring intervention",
            },
            {
                "label": "Highest Incident System",
                "value": highest_incident["system_display"],
                "detail": f"{highest_incident['incident_day_rate_pct']:.1f}% incident-day rate",
            },
            {
                "label": "Highest Leak System",
                "value": highest_leak["system_display"],
                "detail": f"{highest_leak['leak_day_rate_pct']:.1f}% leak-day rate",
            },
        ]
    )

    risk_columns = st.columns(2)
    with risk_columns[0]:
        st.altair_chart(
            grouped_rate_chart(summary, "Operational incident and leak exposure by system"),
            use_container_width=True,
        )

    with risk_columns[1]:
        if leak_severity.empty:
            st.info("No leak severity distribution is available for the current filter selection.")
        else:
            st.altair_chart(
                stacked_severity_chart(leak_severity, "Leak severity distribution"),
                use_container_width=True,
            )

    trend_columns = st.columns(2)
    with trend_columns[0]:
        if monthly_trends.empty:
            st.info("Monthly incident trends are unavailable for the current filter selection.")
        else:
            st.altair_chart(
                system_line_chart(
                    monthly_trends,
                    metric="incident_day_rate_pct",
                    title="Monthly operational incident day rate",
                    y_title="Operational Incident Day Rate (%)",
                    value_format=",.1f",
                ),
                use_container_width=True,
            )

    with trend_columns[1]:
        if monthly_trends.empty:
            st.info("Monthly leak trends are unavailable for the current filter selection.")
        else:
            st.altair_chart(
                system_line_chart(
                    monthly_trends,
                    metric="leak_day_rate_pct",
                    title="Monthly leak day rate",
                    y_title="Leak Day Rate (%)",
                    value_format=",.1f",
                ),
                use_container_width=True,
            )

    section_header(
        "Risk Ranking",
        "A compact view of which systems are currently safest and which need the fastest intervention.",
    )
    render_rank_table(rank_tables["risk"], "Risk Resilience Score", "risk_resilience_score")

    section_header(
        "Alert Feed",
        "Rule-based alerts translate raw observations into an actionable review queue.",
    )
    if alerts.empty:
        st.info("No rule-based alerts were triggered in the current filtered view.")
    else:
        alert_table = alerts.rename(
            columns={
                "date": "Date",
                "system_display": "System",
                "alert_level": "Alert Level",
                "alert_type": "Alert Type",
                "headline": "Headline",
                "detail": "Detail",
            }
        ).copy()
        alert_table["Date"] = alert_table["Date"].apply(format_date)
        st.dataframe(alert_table, use_container_width=True, hide_index=True)

    section_header(
        "Operational Issue Patterns",
        "The main issue categories by system help show whether the risk is recurring and where action should focus.",
    )
    if issue_patterns.empty:
        st.info("No issue-pattern categories are available for the current selection.")
    else:
        st.dataframe(
            issue_patterns.rename(
                columns={
                    "system_display": "System",
                    "issue_category": "Issue Category",
                    "issue_count": "Issue Count",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )

    render_note_block("Recommended Risk Actions", recommendations[:4], style="accent")
    render_footer_tools(filtered_df, outcome_context, cost_model, filters["decision_mode"])


def render_system_comparison_page(
    filtered_df: pd.DataFrame,
    analysis: dict[str, object],
    filters: dict[str, object],
    outcome_context: OutcomeContext,
    cost_model: CostModel,
    comparison_context: dict[str, object],
) -> None:
    summary = analysis["summary"]
    winner_map = analysis["winner_map"]
    score_breakdown = analysis["score_breakdown"]
    explainability = analysis["explainability"]
    confidence_summary = analysis["confidence_summary"]
    limitations = analysis["limitations"]
    rank_tables = analysis["rank_tables"]

    best_overall = winner_map["Best Overall System"]["system"]
    best_efficiency = winner_map["Best Efficiency System"]["system"]
    lowest_risk = winner_map["Lowest Risk System"]["system"]
    lowest_confidence = (
        confidence_summary.sort_values("confidence_score", ascending=True).iloc[0]["system_display"]
        if not confidence_summary.empty
        else "Not available"
    )

    render_hero(
        "System Comparison",
        filters,
        [
            ("Best Overall", best_overall),
            ("Best Efficiency", best_efficiency),
            ("Lowest Risk", lowest_risk),
            ("Lowest Confidence", lowest_confidence),
        ],
    )
    render_note_block("Comparison Limits", limitations[:4], style="warning")

    section_header(
        "Category Winners",
        "Which system currently wins by overall score, cost, efficiency, and risk.",
    )
    render_winner_cards(winner_map)

    section_header(
        "Ranking Tables",
        "Overall, efficiency, and risk rankings under the current decision mode.",
    )
    ranking_columns = st.columns(3, gap="medium")
    with ranking_columns[0]:
        render_compact_rank_table(rank_tables["overall"], "overall_performance_score", "Overall Score")
    with ranking_columns[1]:
        render_compact_rank_table(rank_tables["efficiency"], "efficiency_score", "Efficiency Score")
    with ranking_columns[2]:
        render_compact_rank_table(rank_tables["risk"], "risk_resilience_score", "Risk Score")

    section_header(
        "System Comparison Table",
        "Performance, cost, resource intensity, and risk side by side.",
    )
    _render_system_comparison_table(summary, outcome_context)

    section_header(
        "Why Each System Lands Here",
        "Plain-English explainability so the score does not feel like a black box.",
    )
    render_explainability_table(explainability)

    section_header(
        "Trade-Off Views",
        "Use these views to identify dominant systems and understand what the score is rewarding.",
    )
    chart_columns = st.columns(2, gap="medium")
    with chart_columns[0]:
        st.altair_chart(
            pareto_frontier_chart(
                summary,
                x_metric="estimated_cost_per_100_plants",
                y_metric="incident_day_rate_pct",
                title="Cost vs risk frontier",
                x_title="Estimated Cost per 100 Plants ($)",
                y_title="Operational Incident Day Rate (%)",
            ),
            use_container_width=True,
        )
    with chart_columns[1]:
        if score_breakdown.empty:
            st.info("Score breakdown is unavailable for the current selection.")
        else:
            st.altair_chart(
                score_breakdown_chart(score_breakdown, "Score breakdown by system"),
                use_container_width=True,
            )

    section_header(
        "Confidence And Fairness",
        "Confidence signals show where cross-system comparisons are stronger and where caution is needed.",
    )
    render_confidence_table(confidence_summary)
    render_footer_tools(filtered_df, outcome_context, cost_model, filters["decision_mode"])


def render_scenario_page(
    filtered_df: pd.DataFrame,
    analysis: dict[str, object],
    filters: dict[str, object],
    outcome_context: OutcomeContext,
    cost_model: CostModel,
    comparison_context: dict[str, object],
) -> None:
    base_summary = analysis["summary"]
    section_header(
        "Scenario Controls",
        "Adjust assumption inputs to see how rankings and modeled costs respond under a different operating scenario.",
    )
    control_columns = st.columns(4, gap="small")
    with control_columns[0]:
        scenario_water_cost = st.number_input(
            "Water Cost Per L ($)",
            min_value=0.0,
            value=float(cost_model.water_cost_per_l),
            step=0.0005,
            format="%.4f",
            key="scenario_water_cost",
        )
    with control_columns[1]:
        scenario_nutrient_cost = st.number_input(
            "Nutrient Cost Per mL ($)",
            min_value=0.0,
            value=float(cost_model.nutrient_cost_per_ml),
            step=0.0005,
            format="%.4f",
            key="scenario_nutrient_cost",
        )
    with control_columns[2]:
        scenario_energy_cost = st.number_input(
            "Energy Cost Per Active Day ($)",
            min_value=0.0,
            value=float(cost_model.energy_cost_per_active_day),
            step=0.25,
            format="%.2f",
            key="scenario_energy_cost",
        )
    with control_columns[3]:
        scenario_yield_multiplier = st.number_input(
            "Yield Multiplier",
            min_value=0.50,
            value=1.0,
            step=0.05,
            format="%.2f",
            disabled=not outcome_context.has_yield,
            key="scenario_yield_multiplier",
        )
    if not outcome_context.has_yield:
        st.caption("Yield multiplier is disabled because the current dataset does not contain a usable harvest or yield column.")

    scenario_cost_model = CostModel(
        water_cost_per_l=scenario_water_cost,
        nutrient_cost_per_ml=scenario_nutrient_cost,
        energy_cost_per_active_day=scenario_energy_cost,
    )
    scenario_summary = build_scenario_summary(
        filtered_df,
        scenario_cost_model,
        outcome_context,
        filters["decision_mode"],
        comparison_context,
        yield_multiplier=scenario_yield_multiplier,
    )
    scenario_comparison = build_scenario_comparison(base_summary, scenario_summary)
    scenario_winner_map = build_winner_map(scenario_summary, outcome_context)
    scenario_winner = (
        scenario_summary.sort_values("overall_performance_score", ascending=False).iloc[0]["system_display"]
        if not scenario_summary.empty
        else "Not available"
    )
    base_winner = base_summary.sort_values("overall_performance_score", ascending=False).iloc[0]["system_display"]
    total_base_cost = base_summary["total_estimated_cost"].sum()
    total_scenario_cost = scenario_summary["total_estimated_cost"].sum()
    biggest_shift = (
        scenario_comparison.iloc[0]["system_display"]
        if not scenario_comparison.empty
        else "No shift"
    )

    render_hero(
        "Scenario Simulation",
        filters,
        [
            ("Base Recommendation", base_winner),
            ("Scenario Recommendation", scenario_winner_map.get("Best Overall System", {}).get("system", scenario_winner)),
            ("Scenario Portfolio Cost", format_currency(total_scenario_cost, 2)),
            ("Biggest Ranking Mover", biggest_shift),
        ],
    )
    render_note_block(
        "Scenario Guidance",
        [
            "Use this page to pressure-test the recommendation under different input-cost assumptions.",
            "Yield multiplier is a future-ready placeholder and only affects rankings once yield data exists.",
        ],
        style="soft",
    )

    section_header(
        "Scenario Outcome",
        "How the active assumptions change total cost, system rankings, and the preferred operating choice.",
    )
    cost_delta = total_scenario_cost - total_base_cost
    render_metric_panels(
        [
            {
                "label": "Scenario Recommendation",
                "value": scenario_winner,
                "detail": f"Base recommendation: {base_winner}",
            },
            {
                "label": "Portfolio Cost Delta",
                "value": format_currency(cost_delta, 2),
                "detail": f"From {format_currency(total_base_cost, 2)} to {format_currency(total_scenario_cost, 2)}",
            },
            {
                "label": "Decision Mode",
                "value": filters["decision_mode"],
                "detail": DECISION_MODE_COPY[filters["decision_mode"]],
            },
            {
                "label": "Comparison Basis",
                "value": comparison_context["applied_basis"],
                "detail": comparison_context["basis_note"],
            },
        ]
    )

    chart_columns = st.columns(2, gap="medium")
    with chart_columns[0]:
        st.altair_chart(
            system_bar_chart(
                scenario_summary,
                metric="estimated_cost_per_100_plants",
                title="Scenario cost intensity by system",
                x_title="Estimated Cost per 100 Plants ($)",
                color=COLORS["cost"],
                value_format=",.2f",
            ),
            use_container_width=True,
        )
    with chart_columns[1]:
        st.altair_chart(
            pareto_frontier_chart(
                scenario_summary,
                x_metric="estimated_cost_per_100_plants",
                y_metric="incident_day_rate_pct",
                title="Scenario cost vs risk frontier",
                x_title="Estimated Cost per 100 Plants ($)",
                y_title="Operational Incident Day Rate (%)",
            ),
            use_container_width=True,
        )

    section_header(
        "Ranking Changes",
        "How each system moves relative to the base model under the new assumptions.",
    )
    if scenario_comparison.empty:
        st.info("Scenario comparison is unavailable for the current selection.")
    else:
        st.dataframe(
            scenario_comparison.rename(
                columns={
                    "system_display": "System",
                    "base_rank": "Base Rank",
                    "scenario_rank": "Scenario Rank",
                    "rank_change": "Rank Change",
                    "base_score": "Base Score",
                    "scenario_score": "Scenario Score",
                    "base_cost_per_100_plants": "Base Cost per 100 Plants ($)",
                    "scenario_cost_per_100_plants": "Scenario Cost per 100 Plants ($)",
                    "cost_delta": "Portfolio Cost Delta ($)",
                    "cost_delta_pct": "Portfolio Cost Delta (%)",
                }
            ),
            use_container_width=True,
            hide_index=True,
            column_config={
                "Base Score": st.column_config.NumberColumn(format="%.1f"),
                "Scenario Score": st.column_config.NumberColumn(format="%.1f"),
                "Base Cost per 100 Plants ($)": st.column_config.NumberColumn(format="%.2f"),
                "Scenario Cost per 100 Plants ($)": st.column_config.NumberColumn(format="%.2f"),
                "Portfolio Cost Delta ($)": st.column_config.NumberColumn(format="%.2f"),
                "Portfolio Cost Delta (%)": st.column_config.NumberColumn(format="%.1f"),
            },
        )
    render_footer_tools(filtered_df, outcome_context, cost_model, filters["decision_mode"])


def render_methodology_page(
    filtered_df: pd.DataFrame,
    analysis: dict[str, object],
    filters: dict[str, object],
    outcome_context: OutcomeContext,
    cost_model: CostModel,
    comparison_context: dict[str, object],
) -> None:
    confidence_summary = analysis["confidence_summary"]
    limitations = analysis["limitations"]
    explainability = analysis["explainability"]

    render_hero(
        "Methodology",
        filters,
        [
            ("Scoring Mode", outcome_context.scoring_mode.replace("-", " ").title()),
            ("Decision Mode", filters["decision_mode"]),
            ("Comparison Basis", comparison_context["applied_basis"]),
            ("Systems In Scope", f"{filtered_df['system_display'].nunique():,}"),
        ],
    )

    section_header(
        "Project Objective",
        "Frame the work as a decision-support project rather than a pure dashboard.",
    )
    render_note_block(
        "Objective",
        [
            "Compare greenhouse systems using operational data to support visibility, cost review, and early risk detection.",
            "Provide decision guidance without overstating what the current dataset can prove.",
            "Stay ready for future yield, profitability, and ROI analysis once outcome variables are added.",
        ],
        style="soft",
    )

    section_header(
        "Scoring Logic",
        "How the current weighted model works and why it changes by decision mode.",
    )
    render_note_block(
        "Model Notes",
        [
            outcome_context.readiness_note,
            DECISION_MODE_COPY[filters["decision_mode"]],
            f"Current operating cost assumptions: water {format_currency(cost_model.water_cost_per_l, 4)} per liter, nutrients {format_currency(cost_model.nutrient_cost_per_ml, 4)} per mL, energy {format_currency(cost_model.energy_cost_per_active_day, 2)} per active day.",
        ],
        style="accent",
    )

    section_header(
        "Data Limitations",
        "These caveats should travel with any academic or management presentation of the results.",
    )
    render_note_block("Limitations", limitations, style="warning")

    section_header(
        "Confidence And Comparability",
        "Confidence signals communicate where the system comparison is stronger and where caution is required.",
    )
    render_confidence_table(confidence_summary)

    section_header(
        "Explainability Snapshot",
        "Plain-English score drivers improve transparency and make the model easier to defend.",
    )
    render_explainability_table(explainability)

    section_header(
        "Benchmark And Research Notes",
        "Placeholders for future literature review, benchmark references, and greenhouse best-practice context.",
    )
    render_note_block(
        "Research Placeholder",
        [
            "Add published benchmark ranges for water and nutrient efficiency once a comparable source is selected.",
            "Add greenhouse engineering references for acceptable leak frequency and stability thresholds.",
            "Add yield and harvest definitions before making productivity or profitability claims.",
        ],
        style="soft",
    )
    render_footer_tools(filtered_df, outcome_context, cost_model, filters["decision_mode"])
