
import streamlit as st

def build_analysis_bundle(
    filtered_df,
    cost_model,
    outcome_context,
    filters,
    comparison_context,
):
    recommendations = build_recommendations(

        summary,
        opportunities,
        outcome_context,
        decision_mode,
        confidence_summary,
        comparison_context,
        explainability,
    )
    return {
        "summary": summary,
        "monthly_trends": monthly_trends,
        "opportunities": opportunities,
        "confidence_summary": confidence_summary,
        "explainability": explainability,
        "limitations": limitations,
        "winner_map": winner_map,
        "insights": insights,
        "recommendations": recommendations,
        "alerts": build_alert_feed(filtered_df, cost_model),
        "leak_severity": build_leak_severity_distribution(filtered_df),
        "cost_composition": build_cost_composition(summary),
        "score_breakdown": build_score_breakdown(summary, outcome_context),
        "issue_patterns": build_issue_pattern_summary(filtered_df),
        "rank_tables": build_rank_tables(summary),
    }
def main() -> None:
    inject_styles()
    if not DATA_FILE.exists():
        st.error(f"Could not find the dataset at: {DATA_FILE}")
        st.stop()
    df = load_data()
    outcome_context = detect_outcome_context(df)
    view_mode = render_navigation()
    filters, cost_model = render_controls(df, view_mode)
    filtered_df = apply_filters(df, filters)
    filtered_df, comparison_context = apply_comparison_basis(filtered_df, filters["comparison_basis"])
    comparison_df, _, _, comparison_available = comparison_window(df, filters)
    comparison_df, _ = apply_comparison_basis(comparison_df, filters["comparison_basis"])
    if filtered_df.empty:
        st.warning("No rows match the current filter selections. Adjust the controls to continue.")
        st.stop()
    analysis = build_analysis_bundle(filtered_df, cost_model, outcome_context, filters, comparison_context)
    if analysis["summary"].empty:
        st.warning("The filtered view does not contain enough usable data to build the decision model.")
        st.stop()
    if view_mode == "Dashboard":
        render_dashboard_page(
            filtered_df=filtered_df,
            comparison_df=comparison_df,
            comparison_available=comparison_available,
            analysis=analysis,
            filters=filters,
            outcome_context=outcome_context,
            cost_model=cost_model,
            comparison_context=comparison_context,
        )
    elif view_mode == "System Comparison":
        render_system_comparison_page(
            filtered_df=filtered_df,
            analysis=analysis,
            filters=filters,
            outcome_context=outcome_context,
            cost_model=cost_model,
            comparison_context=comparison_context,
        )
    elif view_mode == "Cost Optimization":
        render_cost_page(
            filtered_df=filtered_df,
            analysis=analysis,
            filters=filters,
            outcome_context=outcome_context,
            cost_model=cost_model,
            comparison_context=comparison_context,
        )
    elif view_mode == "Problem Detection":
        render_problem_page(
            filtered_df=filtered_df,
            analysis=analysis,
            filters=filters,
            outcome_context=outcome_context,
            cost_model=cost_model,
            comparison_context=comparison_context,
        )
    elif view_mode == "Scenario Simulation":
        render_scenario_page(
            filtered_df=filtered_df,
            analysis=analysis,
            filters=filters,
            outcome_context=outcome_context,
            cost_model=cost_model,
            comparison_context=comparison_context,
        )
    else:
        render_methodology_page(
            filtered_df=filtered_df,
            analysis=analysis,
            filters=filters,
            outcome_context=outcome_context,
            cost_model=cost_model,
            comparison_context=comparison_context,
        )
if __name__ == "__main__":
    main()

