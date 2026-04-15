from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .config import (
    COMPARISON_BASIS_OPTIONS,
    DECISION_MODE_COPY,
    AREA_CANDIDATES,
    DEFAULT_COST_MODEL,
    EFFICIENCY_SCORE_WEIGHTS,
    OUTCOME_MODE_WEIGHTS,
    OUTCOME_SCORE_WEIGHTS,
    PROXY_MODE_WEIGHTS,
    PROXY_SCORE_WEIGHTS,
    QUALITY_CANDIDATES,
    RISK_SCORE_WEIGHTS,
    YIELD_CANDIDATES,
)
from .utils import coefficient_of_variation_pct, format_currency, normalize_series, safe_divide


@dataclass(frozen=True)
class CostModel:
    water_cost_per_l: float = DEFAULT_COST_MODEL["water_cost_per_l"]
    nutrient_cost_per_ml: float = DEFAULT_COST_MODEL["nutrient_cost_per_ml"]
    energy_cost_per_active_day: float = DEFAULT_COST_MODEL["energy_cost_per_active_day"]


@dataclass(frozen=True)
class OutcomeContext:
    has_yield: bool
    yield_column: str | None
    area_column: str | None
    quality_column: str | None
    scoring_mode: str
    readiness_note: str


DRIVER_LABELS = {
    "yield_performance": "yield performance",
    "cost_per_kg": "cost per kg",
    "water_per_kg": "water efficiency",
    "nutrient_per_kg": "nutrient efficiency",
    "estimated_cost_per_100_plants": "cost intensity",
    "water_per_100_plants_l": "water intensity",
    "nutrient_per_100_plants_ml": "nutrient intensity",
    "incident_day_rate_pct": "incident control",
    "leak_day_rate_pct": "leak control",
    "daily_water_volatility_pct": "operating stability",
}

DRIVER_GOOD_PHRASES = {
    "yield_performance": "strong yield performance",
    "cost_per_kg": "lower cost per kilogram",
    "water_per_kg": "lower water demand per kilogram",
    "nutrient_per_kg": "lower nutrient demand per kilogram",
    "estimated_cost_per_100_plants": "lower cost intensity",
    "water_per_100_plants_l": "lower water intensity",
    "nutrient_per_100_plants_ml": "lower nutrient intensity",
    "incident_day_rate_pct": "better incident control",
    "leak_day_rate_pct": "better leak control",
    "daily_water_volatility_pct": "steadier day-to-day operations",
}

DRIVER_RISK_PHRASES = {
    "yield_performance": "missing yield evidence",
    "cost_per_kg": "higher cost per kilogram",
    "water_per_kg": "higher water demand per kilogram",
    "nutrient_per_kg": "higher nutrient demand per kilogram",
    "estimated_cost_per_100_plants": "higher cost intensity",
    "water_per_100_plants_l": "higher water intensity",
    "nutrient_per_100_plants_ml": "higher nutrient intensity",
    "incident_day_rate_pct": "higher incident exposure",
    "leak_day_rate_pct": "higher leak exposure",
    "daily_water_volatility_pct": "higher operating volatility",
}


def detect_outcome_context(df: pd.DataFrame) -> OutcomeContext:
    yield_column = next(
        (
            column
            for column in YIELD_CANDIDATES
            if column in df.columns and pd.to_numeric(df[column], errors="coerce").notna().sum() > 0
        ),
        None,
    )
    area_column = next(
        (
            column
            for column in AREA_CANDIDATES
            if column in df.columns and pd.to_numeric(df[column], errors="coerce").notna().sum() > 0
        ),
        None,
    )
    quality_column = next(
        (
            column
            for column in QUALITY_CANDIDATES
            if column in df.columns and pd.to_numeric(df[column], errors="coerce").notna().sum() > 0
        ),
        None,
    )

    if yield_column:
        readiness_note = (
            f"Yield-aware mode is active using `{yield_column}`. Cost-per-kg and water-per-kg "
            "metrics are included in the scoring model."
        )
        return OutcomeContext(
            has_yield=True,
            yield_column=yield_column,
            area_column=area_column,
            quality_column=quality_column,
            scoring_mode="yield-aware",
            readiness_note=readiness_note,
        )

    readiness_note = (
        "Yield or harvest output is not available in the current dataset, so the application is using "
        "an operational proxy score based on cost intensity, resource intensity, stability, and risk."
    )
    return OutcomeContext(
        has_yield=False,
        yield_column=None,
        area_column=area_column,
        quality_column=quality_column,
        scoring_mode="operational-proxy",
        readiness_note=readiness_note,
    )


def resolve_scoring_weights(outcome_context: OutcomeContext, decision_mode: str) -> tuple[dict[str, float], str]:
    if outcome_context.has_yield:
        weight_map = OUTCOME_MODE_WEIGHTS
        if decision_mode == "Yield Maximization":
            scoring_note = "Yield-led weighting is active because a harvest or yield field is available."
        else:
            scoring_note = DECISION_MODE_COPY[decision_mode]
    else:
        weight_map = PROXY_MODE_WEIGHTS
        if decision_mode == "Yield Maximization":
            scoring_note = (
                "Yield Maximization is shown as a future-ready placeholder. Because yield is missing, the "
                "application keeps using an operational proxy model."
            )
        else:
            scoring_note = DECISION_MODE_COPY[decision_mode]
    return weight_map.get(decision_mode, weight_map["Balanced"]), scoring_note


def _metric_label(metric: str) -> str:
    return DRIVER_LABELS.get(metric, metric.replace("_", " ").replace("pct", "").title())


def _system_type_penalty(summary: pd.DataFrame, row: pd.Series) -> float:
    selected_types = set(summary["system_type"].dropna().unique())
    if len(selected_types) <= 1:
        return 0.0
    if row["system_type"] == "Soil" and "Hydroponic" in selected_types:
        return 14.0
    return 0.0


def _system_sort_order(series: pd.Series) -> pd.Series:
    order_map = {"Conventional": 0, "Towers": 1, "A-shape + Gutters": 2}
    return series.map(order_map).fillna(99)


def _weighted_score(frame: pd.DataFrame, weights: dict[str, float], higher_is_better: set[str]) -> pd.DataFrame:
    active_weights = {
        metric: weight
        for metric, weight in weights.items()
        if metric in frame.columns and frame[metric].notna().sum() > 0
    }
    if not active_weights:
        frame["overall_performance_score"] = 0.0
        return frame

    total_weight = sum(active_weights.values())
    weighted_sum = pd.Series([0.0] * len(frame), index=frame.index, dtype=float)
    for metric, weight in active_weights.items():
        metric_score = normalize_series(frame[metric], higher_is_better=metric in higher_is_better)
        frame[f"{metric}_score"] = metric_score
        weighted_sum = weighted_sum.add(metric_score * (weight / total_weight), fill_value=0.0)

    frame["overall_performance_score"] = weighted_sum.round(1)
    return frame


def _subscore(frame: pd.DataFrame, weights: dict[str, float], higher_is_better: set[str], output: str) -> pd.DataFrame:
    active_weights = {
        metric: weight
        for metric, weight in weights.items()
        if metric in frame.columns and frame[metric].notna().sum() > 0
    }
    if not active_weights:
        frame[output] = 0.0
        return frame

    total_weight = sum(active_weights.values())
    weighted_sum = pd.Series([0.0] * len(frame), index=frame.index, dtype=float)
    for metric, weight in active_weights.items():
        weighted_sum = weighted_sum.add(
            normalize_series(frame[metric], higher_is_better=metric in higher_is_better)
            * (weight / total_weight),
            fill_value=0.0,
        )
    frame[output] = weighted_sum.round(1)
    return frame


def build_daily_system_frame(
    filtered_df: pd.DataFrame, cost_model: CostModel, outcome_context: OutcomeContext
) -> pd.DataFrame:
    if filtered_df.empty:
        return pd.DataFrame()

    aggregation = {
        "water_consumption_l": ("water_use_l", "sum"),
        "nutrient_consumption_ml": ("nutrient_total_ml", "sum"),
        "plant_observations": ("plant_count_filled", "sum"),
        "observation_rows": ("system_display", "size"),
        "operational_incidents": ("issue_flag_bool", "sum"),
        "leak_incidents": ("leak_flag_bool", "sum"),
    }
    if outcome_context.has_yield and outcome_context.yield_column:
        aggregation["yield_total"] = (outcome_context.yield_column, "sum")

    daily = (
        filtered_df.dropna(subset=["date_only"])
        .groupby(["date_only", "system_display", "system_type"], as_index=False)
        .agg(**aggregation)
        .rename(columns={"date_only": "date"})
    )

    if daily.empty:
        return daily

    daily["incident_day_flag"] = daily["operational_incidents"] > 0
    daily["leak_day_flag"] = daily["leak_incidents"] > 0
    daily["estimated_water_cost"] = daily["water_consumption_l"] * cost_model.water_cost_per_l
    daily["estimated_nutrient_cost"] = (
        daily["nutrient_consumption_ml"] * cost_model.nutrient_cost_per_ml
    )
    daily["estimated_energy_cost"] = cost_model.energy_cost_per_active_day
    daily["total_estimated_cost"] = (
        daily["estimated_water_cost"]
        + daily["estimated_nutrient_cost"]
        + daily["estimated_energy_cost"]
    )

    return daily


def build_monthly_trends(
    filtered_df: pd.DataFrame, cost_model: CostModel, outcome_context: OutcomeContext
) -> pd.DataFrame:
    daily = build_daily_system_frame(filtered_df, cost_model, outcome_context)
    if daily.empty:
        return pd.DataFrame()

    monthly = daily.copy()
    monthly["month"] = pd.to_datetime(monthly["date"]).dt.to_period("M").dt.to_timestamp()
    summary = (
        monthly.groupby(["month", "system_display", "system_type"], as_index=False)
        .agg(
            active_days=("date", "nunique"),
            water_consumption_l=("water_consumption_l", "sum"),
            nutrient_consumption_ml=("nutrient_consumption_ml", "sum"),
            total_estimated_cost=("total_estimated_cost", "sum"),
            incident_days=("incident_day_flag", "sum"),
            leak_days=("leak_day_flag", "sum"),
        )
        .sort_values(["month", "system_display"])
        .reset_index(drop=True)
    )
    summary["incident_day_rate_pct"] = summary.apply(
        lambda row: safe_divide(row["incident_days"], row["active_days"]) * 100, axis=1
    )
    summary["leak_day_rate_pct"] = summary.apply(
        lambda row: safe_divide(row["leak_days"], row["active_days"]) * 100, axis=1
    )
    return summary


def build_system_summary(
    filtered_df: pd.DataFrame,
    cost_model: CostModel,
    outcome_context: OutcomeContext,
    decision_mode: str = "Balanced",
    comparison_context: dict[str, object] | None = None,
) -> pd.DataFrame:
    daily = build_daily_system_frame(filtered_df, cost_model, outcome_context)
    if daily.empty:
        return pd.DataFrame()

    raw_coverage = (
        filtered_df.groupby(["system_display", "system_type"], as_index=False)
        .agg(
            observation_rows=("system_display", "size"),
            plant_count_observed=("plant_count_imputed", lambda values: (~values).sum()),
        )
        .rename(columns={"system_display": "system_display"})
    )

    crop_summary = (
        filtered_df[["system_display", "crop_type_list"]]
        .explode("crop_type_list")
        .dropna(subset=["crop_type_list"])
        .groupby("system_display", as_index=False)
        .agg(crop_count=("crop_type_list", "nunique"))
    )

    system_summary = (
        daily.groupby(["system_display", "system_type"], as_index=False)
        .agg(
            active_days=("date", "nunique"),
            water_consumption_l=("water_consumption_l", "sum"),
            nutrient_consumption_ml=("nutrient_consumption_ml", "sum"),
            plant_observations=("plant_observations", "sum"),
            observation_rows=("observation_rows", "sum"),
            operational_incidents=("operational_incidents", "sum"),
            leak_incidents=("leak_incidents", "sum"),
            incident_days=("incident_day_flag", "sum"),
            leak_days=("leak_day_flag", "sum"),
            avg_daily_water_l=("water_consumption_l", "mean"),
            avg_daily_nutrient_ml=("nutrient_consumption_ml", "mean"),
            avg_daily_cost=("total_estimated_cost", "mean"),
            total_estimated_cost=("total_estimated_cost", "sum"),
            estimated_water_cost=("estimated_water_cost", "sum"),
            estimated_nutrient_cost=("estimated_nutrient_cost", "sum"),
            estimated_energy_cost=("estimated_energy_cost", "sum"),
            first_active_date=("date", "min"),
            last_active_date=("date", "max"),
        )
        .sort_values("system_display")
        .reset_index(drop=True)
    )

    water_volatility = (
        daily.groupby("system_display")["water_consumption_l"]
        .apply(coefficient_of_variation_pct)
        .rename("daily_water_volatility_pct")
        .reset_index()
    )
    cost_volatility = (
        daily.groupby("system_display")["total_estimated_cost"]
        .apply(coefficient_of_variation_pct)
        .rename("daily_cost_volatility_pct")
        .reset_index()
    )

    system_summary = system_summary.merge(water_volatility, on="system_display", how="left")
    system_summary = system_summary.merge(cost_volatility, on="system_display", how="left")
    system_summary = system_summary.merge(raw_coverage, on=["system_display", "system_type"], how="left", suffixes=("", "_raw"))
    system_summary = system_summary.merge(crop_summary, on="system_display", how="left")
    system_summary["crop_count"] = system_summary["crop_count"].fillna(0).astype(int)
    system_summary["plant_count_coverage_pct"] = system_summary.apply(
        lambda row: safe_divide(row["plant_count_observed"], row["observation_rows_raw"]) * 100,
        axis=1,
    )

    system_summary["water_per_100_plants_l"] = system_summary.apply(
        lambda row: safe_divide(row["water_consumption_l"], row["plant_observations"]) * 100,
        axis=1,
    )
    system_summary["nutrient_per_100_plants_ml"] = system_summary.apply(
        lambda row: safe_divide(row["nutrient_consumption_ml"], row["plant_observations"]) * 100,
        axis=1,
    )
    system_summary["estimated_cost_per_100_plants"] = system_summary.apply(
        lambda row: safe_divide(row["total_estimated_cost"], row["plant_observations"]) * 100,
        axis=1,
    )
    system_summary["incident_day_rate_pct"] = system_summary.apply(
        lambda row: safe_divide(row["incident_days"], row["active_days"]) * 100,
        axis=1,
    )
    system_summary["leak_day_rate_pct"] = system_summary.apply(
        lambda row: safe_divide(row["leak_days"], row["active_days"]) * 100,
        axis=1,
    )
    system_summary["incident_intensity_per_day"] = system_summary.apply(
        lambda row: safe_divide(row["operational_incidents"], row["active_days"]),
        axis=1,
    )
    system_summary["leak_intensity_per_day"] = system_summary.apply(
        lambda row: safe_divide(row["leak_incidents"], row["active_days"]),
        axis=1,
    )

    total_cost = system_summary["total_estimated_cost"].sum()
    system_summary["cost_share_pct"] = system_summary.apply(
        lambda row: safe_divide(row["total_estimated_cost"], total_cost) * 100, axis=1
    )

    if outcome_context.has_yield and outcome_context.yield_column:
        yield_summary = (
            filtered_df.groupby(["system_display", "system_type"], as_index=False)
            .agg(yield_total=(outcome_context.yield_column, "sum"))
        )
        system_summary = system_summary.merge(yield_summary, on=["system_display", "system_type"], how="left")
        system_summary["yield_total"] = system_summary["yield_total"].fillna(0.0)
        system_summary["yield_per_100_plants"] = system_summary.apply(
            lambda row: safe_divide(row["yield_total"], row["plant_observations"]) * 100,
            axis=1,
        )
        system_summary["cost_per_kg"] = system_summary.apply(
            lambda row: safe_divide(row["total_estimated_cost"], row["yield_total"]), axis=1
        )
        system_summary["water_per_kg"] = system_summary.apply(
            lambda row: safe_divide(row["water_consumption_l"], row["yield_total"]), axis=1
        )
        system_summary["nutrient_per_kg"] = system_summary.apply(
            lambda row: safe_divide(row["nutrient_consumption_ml"], row["yield_total"]), axis=1
        )
        system_summary["water_efficiency"] = system_summary.apply(
            lambda row: safe_divide(row["yield_total"], row["water_consumption_l"]), axis=1
        )
        system_summary["nutrient_efficiency"] = system_summary.apply(
            lambda row: safe_divide(row["yield_total"], row["nutrient_consumption_ml"]), axis=1
        )
        system_summary["cost_efficiency"] = system_summary.apply(
            lambda row: safe_divide(row["yield_total"], row["total_estimated_cost"]), axis=1
        )
    else:
        system_summary["yield_total"] = float("nan")
        system_summary["yield_per_100_plants"] = float("nan")
        system_summary["cost_per_kg"] = float("nan")
        system_summary["water_per_kg"] = float("nan")
        system_summary["nutrient_per_kg"] = float("nan")
        system_summary["water_efficiency"] = float("nan")
        system_summary["nutrient_efficiency"] = float("nan")
        system_summary["cost_efficiency"] = float("nan")

    score_weights, scoring_note = resolve_scoring_weights(outcome_context, decision_mode)
    higher_is_better = {"yield_performance"}
    if outcome_context.has_yield:
        system_summary["yield_performance"] = system_summary["yield_per_100_plants"]
    system_summary = _weighted_score(system_summary, score_weights, higher_is_better)
    system_summary = _subscore(
        system_summary,
        EFFICIENCY_SCORE_WEIGHTS,
        higher_is_better=set(),
        output="efficiency_score",
    )
    system_summary = _subscore(
        system_summary,
        RISK_SCORE_WEIGHTS,
        higher_is_better=set(),
        output="risk_resilience_score",
    )
    system_summary["risk_resilience_score"] = system_summary["risk_resilience_score"].round(1)
    system_summary["efficiency_score"] = system_summary["efficiency_score"].round(1)
    system_summary["score_gap_from_leader"] = (
        system_summary["overall_performance_score"].max() - system_summary["overall_performance_score"]
    ).round(1)
    system_summary["decision_mode"] = decision_mode
    system_summary["scoring_note"] = scoring_note
    system_summary["nutrient_recorded_flag"] = system_summary["nutrient_consumption_ml"] > 0
    if comparison_context:
        system_summary["comparison_basis"] = comparison_context["applied_basis"]
        system_summary["comparison_note"] = comparison_context["basis_note"]
    else:
        system_summary["comparison_basis"] = COMPARISON_BASIS_OPTIONS[0]
        system_summary["comparison_note"] = "The full filtered dataset is shown."
    system_summary["system_sort"] = _system_sort_order(system_summary["system_display"])

    return system_summary.sort_values(["system_sort", "system_display"]).reset_index(drop=True)


def build_confidence_summary(
    filtered_df: pd.DataFrame,
    summary: pd.DataFrame,
    comparison_context: dict[str, object] | None,
) -> pd.DataFrame:
    if filtered_df.empty or summary.empty:
        return pd.DataFrame()

    coverage = (
        comparison_context["coverage"].copy()
        if comparison_context and not comparison_context.get("coverage", pd.DataFrame()).empty
        else filtered_df.groupby("system_display", as_index=False)
        .agg(
            system_start=("date_only", "min"),
            system_end=("date_only", "max"),
            active_days_raw=("date_only", "nunique"),
            rows_raw=("system_display", "size"),
        )
    )
    coverage = coverage.rename(
        columns={
            "active_days": "active_days_raw",
            "rows": "rows_raw",
        }
    )
    overlap_available = bool(comparison_context and comparison_context.get("overlap_available"))
    overlap_start = comparison_context.get("overlap_start") if comparison_context else None
    overlap_end = comparison_context.get("overlap_end") if comparison_context else None
    selected_days = comparison_context.get("selected_days", 0) if comparison_context else 0
    overlap_days = comparison_context.get("overlap_days", 0) if comparison_context else 0
    reference_days = overlap_days if comparison_context and comparison_context.get("overlap_applied") else selected_days
    reference_days = max(reference_days or 0, 1)

    overlap_active = pd.DataFrame(columns=["system_display", "active_overlap_days"])
    if overlap_available and overlap_start and overlap_end:
        overlap_active = (
            filtered_df[filtered_df["date_only"].between(overlap_start, overlap_end, inclusive="both")]
            .groupby("system_display", as_index=False)
            .agg(active_overlap_days=("date_only", "nunique"))
        )

    confidence = summary[
        [
            "system_display",
            "system_type",
            "active_days",
            "observation_rows",
            "plant_observations",
            "water_consumption_l",
            "nutrient_consumption_ml",
            "plant_count_coverage_pct",
        ]
    ].copy()
    confidence = confidence.merge(coverage, on="system_display", how="left")
    confidence = confidence.merge(overlap_active, on="system_display", how="left")
    confidence["active_overlap_days"] = confidence["active_overlap_days"].fillna(confidence["active_days"])
    confidence["window_coverage_pct"] = confidence.apply(
        lambda row: safe_divide(row["active_days"], reference_days) * 100,
        axis=1,
    )
    if overlap_available and overlap_days > 0:
        confidence["date_alignment_pct"] = confidence.apply(
            lambda row: safe_divide(row["active_overlap_days"], overlap_days) * 100,
            axis=1,
        )
    else:
        confidence["date_alignment_pct"] = 100.0

    max_rows = max(confidence["observation_rows"].max(), 1)
    confidence["signal_strength_pct"] = confidence["observation_rows"].apply(
        lambda value: safe_divide(value, max_rows) * 100
    )

    median_plants = confidence["plant_observations"].replace(0, pd.NA).median()
    median_plants = median_plants if pd.notna(median_plants) and median_plants > 0 else 1.0

    def scale_alignment(row: pd.Series) -> float:
        ratio = safe_divide(row["plant_observations"], median_plants)
        gap = abs(ratio - 1)
        return max(35.0, 100.0 - min(gap * 35.0, 55.0))

    confidence["scale_alignment_pct"] = confidence.apply(scale_alignment, axis=1)
    nutrient_tracking_gap = (
        confidence["nutrient_consumption_ml"].eq(0) & confidence["system_type"].eq("Soil")
    )
    confidence["measurement_alignment_pct"] = 100.0
    confidence.loc[nutrient_tracking_gap, "measurement_alignment_pct"] = 72.0
    confidence["measurement_alignment_pct"] = confidence.apply(
        lambda row: max(55.0, row["measurement_alignment_pct"] - _system_type_penalty(confidence, row)),
        axis=1,
    )

    confidence["imputation_rate_pct"] = 100 - confidence["plant_count_coverage_pct"].fillna(0.0)
    confidence["comparability_score"] = (
        confidence["date_alignment_pct"] * 0.45
        + confidence["scale_alignment_pct"] * 0.25
        + confidence["measurement_alignment_pct"] * 0.30
    ).round(1)
    confidence["confidence_score"] = (
        confidence["plant_count_coverage_pct"].fillna(0.0) * 0.35
        + confidence["window_coverage_pct"] * 0.20
        + confidence["signal_strength_pct"] * 0.20
        + confidence["comparability_score"] * 0.25
    ).round(1)

    def confidence_label(value: float) -> str:
        if value >= 78:
            return "High"
        if value >= 62:
            return "Moderate"
        return "Caution"

    def warning_bundle(row: pd.Series) -> str:
        warnings: list[str] = []
        if row["imputation_rate_pct"] >= 20:
            warnings.append("plant counts rely on imputation")
        if row["date_alignment_pct"] < 70:
            warnings.append("date coverage is weakly aligned with peers")
        if row["signal_strength_pct"] < 55 or row["active_days"] < 28:
            warnings.append("operational signal is relatively thin")
        if row["measurement_alignment_pct"] < 85:
            warnings.append("measurement basis is not fully comparable")
        if not warnings:
            warnings.append("comparability is reasonable inside the current selection")
        return "; ".join(warnings[:2])

    confidence["confidence_label"] = confidence["confidence_score"].apply(confidence_label)
    confidence["warning_summary"] = confidence.apply(warning_bundle, axis=1)
    confidence["trust_note"] = confidence.apply(
        lambda row: (
            f"{row['confidence_label']} confidence. {row['warning_summary'].capitalize()}."
        ),
        axis=1,
    )
    return confidence.sort_values(
        ["confidence_score", "signal_strength_pct"], ascending=[False, False]
    ).reset_index(drop=True)


def build_limitations_notes(
    summary: pd.DataFrame,
    outcome_context: OutcomeContext,
    comparison_context: dict[str, object] | None,
    confidence_summary: pd.DataFrame,
) -> list[str]:
    notes = [outcome_context.readiness_note]

    if comparison_context:
        notes.append(comparison_context["basis_note"])
        if comparison_context.get("applied_basis") == COMPARISON_BASIS_OPTIONS[0] and comparison_context.get(
            "overlap_available"
        ):
            notes.append(
                "Cross-system observation windows are not fully aligned, so seasonality and timing may still influence direct comparisons."
            )

    if not confidence_summary.empty:
        lowest_confidence = confidence_summary.sort_values("confidence_score", ascending=True).iloc[0]
        if lowest_confidence["confidence_label"] != "High":
            notes.append(
                f"{lowest_confidence['system_display']} carries lower comparison confidence because {lowest_confidence['warning_summary']}."
            )

    if not summary.empty and (summary["system_type"] == "Soil").any() and (summary["nutrient_consumption_ml"] == 0).any():
        notes.append(
            "Conventional soil observations do not capture nutrient inputs in the same way hydroponic systems do, so cross-system cost comparisons should be treated carefully."
        )

    return notes[:4]


def build_score_explanations(
    summary: pd.DataFrame,
    outcome_context: OutcomeContext,
    decision_mode: str,
    confidence_summary: pd.DataFrame | None = None,
) -> pd.DataFrame:
    if summary.empty:
        return pd.DataFrame()

    weights, scoring_note = resolve_scoring_weights(outcome_context, decision_mode)
    active_weights = {
        metric: weight
        for metric, weight in weights.items()
        if f"{metric}_score" in summary.columns and summary[f"{metric}_score"].notna().sum() > 0
    }
    if not active_weights:
        return pd.DataFrame()

    total_weight = sum(active_weights.values())
    confidence_map = {}
    if confidence_summary is not None and not confidence_summary.empty:
        confidence_map = confidence_summary.set_index("system_display")["trust_note"].to_dict()

    explanation_rows: list[dict[str, object]] = []
    for _, row in summary.iterrows():
        contributions: list[dict[str, object]] = []
        for metric, weight in active_weights.items():
            metric_score = float(row.get(f"{metric}_score", 0.0))
            contributions.append(
                {
                    "metric": metric,
                    "label": _metric_label(metric),
                    "score": metric_score,
                    "weighted_contribution": metric_score * (weight / total_weight),
                }
            )
        contributions = sorted(contributions, key=lambda item: item["weighted_contribution"], reverse=True)
        strongest = contributions[0]
        weakest = sorted(contributions, key=lambda item: item["weighted_contribution"])[0]
        top_driver_list = ", ".join(item["label"] for item in contributions[:3])
        narrative = (
            f"{row['system_display']} ranks well because of {DRIVER_GOOD_PHRASES.get(strongest['metric'], strongest['label'])}, "
            f"but is held back by {DRIVER_RISK_PHRASES.get(weakest['metric'], weakest['label'])}."
        )
        if row["system_display"] in confidence_map:
            narrative = f"{narrative} {confidence_map[row['system_display']]}"

        explanation_rows.append(
            {
                "system_display": row["system_display"],
                "overall_performance_score": row["overall_performance_score"],
                "efficiency_score": row["efficiency_score"],
                "risk_resilience_score": row["risk_resilience_score"],
                "strongest_driver": strongest["label"].title(),
                "weakest_driver": weakest["label"].title(),
                "top_driver_list": top_driver_list.title(),
                "decision_mode": decision_mode,
                "scoring_note": scoring_note,
                "explanation": narrative,
            }
        )

    return pd.DataFrame(explanation_rows).sort_values(
        "overall_performance_score", ascending=False
    ).reset_index(drop=True)


def build_issue_pattern_summary(filtered_df: pd.DataFrame) -> pd.DataFrame:
    if filtered_df.empty:
        return pd.DataFrame()

    issues = (
        filtered_df[["system_display", "issue_category_list"]]
        .explode("issue_category_list")
        .dropna(subset=["issue_category_list"])
    )
    if issues.empty:
        return pd.DataFrame()

    summary = (
        issues.groupby(["system_display", "issue_category_list"], as_index=False)
        .size()
        .rename(columns={"issue_category_list": "issue_category", "size": "issue_count"})
        .sort_values(["system_display", "issue_count"], ascending=[True, False])
        .reset_index(drop=True)
    )
    return summary


def build_scenario_summary(
    filtered_df: pd.DataFrame,
    cost_model: CostModel,
    outcome_context: OutcomeContext,
    decision_mode: str,
    comparison_context: dict[str, object] | None,
    yield_multiplier: float = 1.0,
) -> pd.DataFrame:
    scenario_df = filtered_df.copy()
    if outcome_context.has_yield and outcome_context.yield_column and yield_multiplier != 1.0:
        scenario_df[outcome_context.yield_column] = (
            pd.to_numeric(scenario_df[outcome_context.yield_column], errors="coerce").fillna(0.0)
            * yield_multiplier
        )
    return build_system_summary(
        scenario_df,
        cost_model,
        outcome_context,
        decision_mode=decision_mode,
        comparison_context=comparison_context,
    )


def build_scenario_comparison(base_summary: pd.DataFrame, scenario_summary: pd.DataFrame) -> pd.DataFrame:
    if base_summary.empty or scenario_summary.empty:
        return pd.DataFrame()

    base = base_summary.copy().sort_values("overall_performance_score", ascending=False).reset_index(drop=True)
    scenario = scenario_summary.copy().sort_values("overall_performance_score", ascending=False).reset_index(drop=True)
    base["base_rank"] = base.index + 1
    scenario["scenario_rank"] = scenario.index + 1

    comparison = base[
        [
            "system_display",
            "base_rank",
            "overall_performance_score",
            "estimated_cost_per_100_plants",
            "total_estimated_cost",
        ]
    ].rename(
        columns={
            "overall_performance_score": "base_score",
            "estimated_cost_per_100_plants": "base_cost_per_100_plants",
            "total_estimated_cost": "base_total_cost",
        }
    )
    comparison = comparison.merge(
        scenario[
            [
                "system_display",
                "scenario_rank",
                "overall_performance_score",
                "estimated_cost_per_100_plants",
                "total_estimated_cost",
            ]
        ].rename(
            columns={
                "overall_performance_score": "scenario_score",
                "estimated_cost_per_100_plants": "scenario_cost_per_100_plants",
                "total_estimated_cost": "scenario_total_cost",
            }
        ),
        on="system_display",
        how="left",
    )
    comparison["rank_change"] = comparison["base_rank"] - comparison["scenario_rank"]
    comparison["cost_delta"] = comparison["scenario_total_cost"] - comparison["base_total_cost"]
    comparison["cost_delta_pct"] = comparison.apply(
        lambda row: safe_divide(row["cost_delta"], row["base_total_cost"]) * 100,
        axis=1,
    )
    return comparison.sort_values("scenario_rank").reset_index(drop=True)


def build_rank_tables(summary: pd.DataFrame) -> dict[str, pd.DataFrame]:
    if summary.empty:
        return {"overall": pd.DataFrame(), "efficiency": pd.DataFrame(), "risk": pd.DataFrame()}

    def _rank_frame(metric: str, ascending: bool, label: str) -> pd.DataFrame:
        ranked = summary[
            [
                "system_display",
                "system_type",
                "overall_performance_score",
                "efficiency_score",
                "risk_resilience_score",
                "estimated_cost_per_100_plants",
                "incident_day_rate_pct",
                "leak_day_rate_pct",
            ]
        ].copy()
        ranked = ranked.sort_values(metric, ascending=ascending).reset_index(drop=True)
        ranked.insert(0, "rank", ranked.index + 1)
        ranked["ranking_view"] = label
        return ranked

    return {
        "overall": _rank_frame("overall_performance_score", ascending=False, label="Overall"),
        "efficiency": _rank_frame("efficiency_score", ascending=False, label="Efficiency"),
        "risk": _rank_frame("risk_resilience_score", ascending=False, label="Risk"),
    }


def build_cost_composition(summary: pd.DataFrame) -> pd.DataFrame:
    if summary.empty:
        return pd.DataFrame()

    composition = summary[
        [
            "system_display",
            "estimated_water_cost",
            "estimated_nutrient_cost",
            "estimated_energy_cost",
        ]
    ].melt(
        id_vars="system_display",
        var_name="cost_component",
        value_name="cost_value",
    )
    label_map = {
        "estimated_water_cost": "Water",
        "estimated_nutrient_cost": "Nutrients",
        "estimated_energy_cost": "Energy",
    }
    composition["cost_component"] = composition["cost_component"].map(label_map)
    return composition


def build_leak_severity_distribution(filtered_df: pd.DataFrame) -> pd.DataFrame:
    if filtered_df.empty:
        return pd.DataFrame()

    leak_df = filtered_df[filtered_df["leak_flag_bool"]].copy()
    if leak_df.empty:
        return pd.DataFrame()

    summary = (
        leak_df.groupby(["system_display", "leak_severity_label"], as_index=False)
        .size()
        .rename(columns={"leak_severity_label": "leak_severity", "size": "leak_incidents"})
    )
    summary["system_sort"] = _system_sort_order(summary["system_display"])
    severity_order = {"Major": 0, "Minor": 1, "Unspecified": 2, "Unknown": 3}
    summary["severity_sort"] = summary["leak_severity"].map(severity_order).fillna(99)
    return summary.sort_values(["system_sort", "severity_sort"]).reset_index(drop=True)


def build_optimization_opportunities(
    summary: pd.DataFrame, cost_model: CostModel, outcome_context: OutcomeContext
) -> pd.DataFrame:
    if summary.empty:
        return pd.DataFrame()

    best_water = summary["water_per_100_plants_l"].replace(0, pd.NA).dropna().min()
    best_nutrient = summary["nutrient_per_100_plants_ml"].replace(0, pd.NA).dropna().min()
    best_cost = summary["estimated_cost_per_100_plants"].replace(0, pd.NA).dropna().min()
    median_incident_rate = summary["incident_day_rate_pct"].median()
    median_leak_rate = summary["leak_day_rate_pct"].median()

    opportunities = summary.copy()
    opportunities["potential_water_savings_l"] = (
        ((opportunities["water_per_100_plants_l"] - best_water).clip(lower=0) / 100)
        * opportunities["plant_observations"]
    )
    opportunities["potential_nutrient_savings_ml"] = (
        ((opportunities["nutrient_per_100_plants_ml"] - best_nutrient).clip(lower=0) / 100)
        * opportunities["plant_observations"]
    )
    opportunities["potential_cost_savings"] = (
        opportunities["potential_water_savings_l"] * cost_model.water_cost_per_l
        + opportunities["potential_nutrient_savings_ml"] * cost_model.nutrient_cost_per_ml
        + (((opportunities["estimated_cost_per_100_plants"] - best_cost).clip(lower=0) / 100)
           * opportunities["plant_observations"] * 0.15)
    ).round(2)

    def describe(row: pd.Series) -> str:
        notes: list[str] = []
        if row["water_per_100_plants_l"] > best_water:
            notes.append("water-heavy")
        if row["nutrient_per_100_plants_ml"] > best_nutrient and row["nutrient_consumption_ml"] > 0:
            notes.append("nutrient-heavy")
        if row["incident_day_rate_pct"] > median_incident_rate:
            notes.append("incident-prone")
        if row["leak_day_rate_pct"] > median_leak_rate and row["leak_day_rate_pct"] > 0:
            notes.append("leak-exposed")
        if not notes:
            notes.append("maintain current operating discipline")
        return ", ".join(notes)

    def priority(row: pd.Series) -> str:
        if row["potential_cost_savings"] >= opportunities["potential_cost_savings"].quantile(0.66):
            return "High"
        if row["potential_cost_savings"] > 0 or row["incident_day_rate_pct"] > median_incident_rate:
            return "Medium"
        return "Maintain"

    opportunities["opportunity_profile"] = opportunities.apply(describe, axis=1)
    opportunities["priority"] = opportunities.apply(priority, axis=1)
    if not outcome_context.has_yield:
        opportunities["opportunity_basis"] = "Operational proxy"
    else:
        opportunities["opportunity_basis"] = "Yield-aware"

    return opportunities.sort_values(
        ["potential_cost_savings", "incident_day_rate_pct"], ascending=[False, False]
    ).reset_index(drop=True)


def build_alert_feed(filtered_df: pd.DataFrame, cost_model: CostModel) -> pd.DataFrame:
    if filtered_df.empty:
        return pd.DataFrame()

    daily = (
        filtered_df.dropna(subset=["date_only"])
        .groupby(["date_only", "system_display"], as_index=False)
        .agg(
            water_consumption_l=("water_use_l", "sum"),
            nutrient_consumption_ml=("nutrient_total_ml", "sum"),
            operational_incidents=("issue_flag_bool", "sum"),
            leak_incidents=("leak_flag_bool", "sum"),
            plant_observations=("plant_count_filled", "sum"),
        )
        .rename(columns={"date_only": "date"})
    )
    if daily.empty:
        return daily

    daily["total_estimated_cost"] = (
        daily["water_consumption_l"] * cost_model.water_cost_per_l
        + daily["nutrient_consumption_ml"] * cost_model.nutrient_cost_per_ml
        + cost_model.energy_cost_per_active_day
    )
    mean_by_system = daily.groupby("system_display")["water_consumption_l"].transform("mean")
    std_by_system = daily.groupby("system_display")["water_consumption_l"].transform("std").fillna(0.0)
    threshold = (mean_by_system + std_by_system).where(std_by_system > 0, mean_by_system * 1.4)
    daily["water_spike_flag"] = daily["water_consumption_l"] > threshold
    daily["water_vs_average_pct"] = (
        daily.apply(lambda row: safe_divide(row["water_consumption_l"], mean_by_system.loc[row.name]) - 1, axis=1)
        * 100
    )
    cost_mean = daily.groupby("system_display")["total_estimated_cost"].transform("mean")
    cost_std = daily.groupby("system_display")["total_estimated_cost"].transform("std").fillna(0.0)
    cost_threshold = (cost_mean + cost_std).where(cost_std > 0, cost_mean * 1.35)
    daily["cost_spike_flag"] = daily["total_estimated_cost"] > cost_threshold
    daily["cost_vs_average_pct"] = (
        daily.apply(lambda row: safe_divide(row["total_estimated_cost"], cost_mean.loc[row.name]) - 1, axis=1) * 100
    )
    daily = daily.sort_values(["system_display", "date"]).reset_index(drop=True)
    daily["incident_day_flag"] = daily["operational_incidents"] > 0
    daily["leak_day_flag"] = daily["leak_incidents"] > 0
    daily["incident_trend_7d"] = (
        daily.groupby("system_display")["incident_day_flag"]
        .transform(lambda values: values.rolling(7, min_periods=3).mean())
        .fillna(0.0)
    )
    daily["leak_cluster_7d"] = (
        daily.groupby("system_display")["leak_day_flag"]
        .transform(lambda values: values.rolling(7, min_periods=3).sum())
        .fillna(0.0)
    )
    daily["water_volatility_7d"] = (
        daily.groupby("system_display")["water_consumption_l"]
        .transform(lambda values: values.rolling(7, min_periods=4).std(ddof=0))
        .fillna(0.0)
    )
    system_water_baseline = daily.groupby("system_display")["water_consumption_l"].transform("std").fillna(0.0)

    alerts: list[dict[str, object]] = []
    for _, row in daily.iterrows():
        if row["leak_incidents"] > 0:
            alerts.append(
                {
                    "date": row["date"],
                    "system_display": row["system_display"],
                    "alert_level": "Critical",
                    "alert_type": "Leak Incident",
                    "headline": f"{row['system_display']} recorded leak activity.",
                    "detail": (
                        f"{int(row['leak_incidents'])} leak incident(s) were recorded during the day and should "
                        "be inspected immediately."
                    ),
                }
            )
        if row["operational_incidents"] > 0:
            alerts.append(
                {
                    "date": row["date"],
                    "system_display": row["system_display"],
                    "alert_level": "Warning",
                    "alert_type": "Operational Incident",
                    "headline": f"{row['system_display']} recorded operational incidents.",
                    "detail": (
                        f"{int(row['operational_incidents'])} incident(s) were logged and may indicate unstable operations."
                    ),
                }
            )
        if row["water_spike_flag"]:
            alerts.append(
                {
                    "date": row["date"],
                    "system_display": row["system_display"],
                    "alert_level": "Flag",
                    "alert_type": "Water Spike",
                    "headline": f"{row['system_display']} exceeded its usual water pattern.",
                    "detail": (
                        f"Water consumption ran {row['water_vs_average_pct']:.1f}% above the system's average day."
                    ),
                }
            )
        if row["cost_spike_flag"]:
            alerts.append(
                {
                    "date": row["date"],
                    "system_display": row["system_display"],
                    "alert_level": "Flag",
                    "alert_type": "Cost Spike",
                    "headline": f"{row['system_display']} posted an unusual daily cost spike.",
                    "detail": (
                        f"Estimated daily operating cost was {row['cost_vs_average_pct']:.1f}% above the system's average."
                    ),
                }
            )
        if row["incident_trend_7d"] >= 0.45 and row["operational_incidents"] > 0:
            alerts.append(
                {
                    "date": row["date"],
                    "system_display": row["system_display"],
                    "alert_level": "Warning",
                    "alert_type": "Rising Incident Trend",
                    "headline": f"{row['system_display']} is showing a rising incident pattern.",
                    "detail": "Recent incident frequency is elevated versus the system's normal operating rhythm.",
                }
            )
        if row["leak_cluster_7d"] >= 2 and row["leak_incidents"] > 0:
            alerts.append(
                {
                    "date": row["date"],
                    "system_display": row["system_display"],
                    "alert_level": "Critical",
                    "alert_type": "Leak Cluster",
                    "headline": f"{row['system_display']} is showing clustered leak activity.",
                    "detail": "Multiple leak days were detected within a short operating window, increasing loss risk.",
                }
            )
        if row["water_volatility_7d"] > system_water_baseline.loc[_] * 1.25 and row["water_volatility_7d"] > 0:
            alerts.append(
                {
                    "date": row["date"],
                    "system_display": row["system_display"],
                    "alert_level": "Flag",
                    "alert_type": "Water Volatility",
                    "headline": f"{row['system_display']} is showing unstable water behavior.",
                    "detail": "Short-term water variability is running above the system's usual day-to-day pattern.",
                }
            )

    if not alerts:
        return pd.DataFrame()

    alert_frame = pd.DataFrame(alerts)
    alert_frame["alert_sort"] = alert_frame["alert_level"].map({"Critical": 0, "Warning": 1, "Flag": 2})
    return alert_frame.sort_values(["alert_sort", "date"], ascending=[True, False]).reset_index(drop=True)


def build_score_breakdown(summary: pd.DataFrame, outcome_context: OutcomeContext) -> pd.DataFrame:
    if summary.empty:
        return pd.DataFrame()

    if outcome_context.has_yield:
        label_map = {
            "yield_performance_score": "Yield performance",
            "cost_per_kg_score": "Cost per kg",
            "water_per_kg_score": "Water per kg",
            "nutrient_per_kg_score": "Nutrients per kg",
            "incident_day_rate_pct_score": "Incident rate",
            "leak_day_rate_pct_score": "Leak rate",
            "daily_water_volatility_pct_score": "Water stability",
        }
    else:
        label_map = {
            "estimated_cost_per_100_plants_score": "Cost intensity",
            "water_per_100_plants_l_score": "Water intensity",
            "nutrient_per_100_plants_ml_score": "Nutrient intensity",
            "incident_day_rate_pct_score": "Incident rate",
            "leak_day_rate_pct_score": "Leak rate",
            "daily_water_volatility_pct_score": "Water stability",
        }

    score_columns = [column for column in label_map if column in summary.columns]
    if not score_columns:
        return pd.DataFrame()

    breakdown = summary[["system_display", *score_columns]].melt(
        id_vars="system_display",
        var_name="score_component",
        value_name="score_value",
    )
    breakdown["score_component"] = breakdown["score_component"].map(label_map)
    return breakdown


def build_winner_map(summary: pd.DataFrame, outcome_context: OutcomeContext) -> dict[str, dict[str, str]]:
    if summary.empty:
        return {}

    lowest_cost_row = summary.sort_values(
        ["estimated_cost_per_100_plants", "total_estimated_cost"], ascending=[True, True]
    ).iloc[0]
    best_efficiency_row = summary.sort_values(
        ["efficiency_score", "overall_performance_score"], ascending=[False, False]
    ).iloc[0]
    lowest_risk_row = summary.sort_values(
        ["risk_resilience_score", "overall_performance_score"], ascending=[False, False]
    ).iloc[0]
    best_overall_row = summary.sort_values("overall_performance_score", ascending=False).iloc[0]

    winner_map = {
        "Best Overall System": {
            "system": best_overall_row["system_display"],
            "metric": f"{best_overall_row['overall_performance_score']:.1f} Overall Performance Score",
            "detail": "Weighted blend of efficiency, risk, and operating discipline.",
        },
        "Lowest Cost System": {
            "system": lowest_cost_row["system_display"],
            "metric": f"{format_currency(lowest_cost_row['estimated_cost_per_100_plants'], 2)} per 100 plants",
            "detail": "Uses normalized estimated cost rather than raw spend so system scale does not dominate.",
        },
        "Best Efficiency System": {
            "system": best_efficiency_row["system_display"],
            "metric": f"{best_efficiency_row['efficiency_score']:.1f} Efficiency Score",
            "detail": "Based on cost, water, and nutrient intensity.",
        },
        "Lowest Risk System": {
            "system": lowest_risk_row["system_display"],
            "metric": f"{lowest_risk_row['risk_resilience_score']:.1f} Risk Resilience Score",
            "detail": "Best balance of incident control, leak control, and stability.",
        },
    }

    if outcome_context.has_yield:
        best_yield_row = summary.sort_values("yield_total", ascending=False).iloc[0]
        winner_map["Best Yield System"] = {
            "system": best_yield_row["system_display"],
            "metric": f"{best_yield_row['yield_total']:,.1f} total yield",
            "detail": "Highest observed outcome volume in the filtered selection.",
        }
    else:
        winner_map["Best Yield System"] = {
            "system": "Not available",
            "metric": "Yield data missing",
            "detail": "Add harvest or yield columns to enable true production benchmarking.",
        }

    return winner_map


def build_executive_summary(
    summary: pd.DataFrame,
    winner_map: dict[str, dict[str, str]],
    opportunities: pd.DataFrame,
    outcome_context: OutcomeContext,
    confidence_summary: pd.DataFrame,
    comparison_context: dict[str, object] | None,
    decision_mode: str,
) -> list[dict[str, str]]:
    if summary.empty:
        return []

    insights: list[dict[str, str]] = []
    leader = summary.sort_values("overall_performance_score", ascending=False).iloc[0]
    runner_up_score = (
        summary["overall_performance_score"].sort_values(ascending=False).iloc[1]
        if len(summary) > 1
        else leader["overall_performance_score"]
    )
    lead_margin = leader["overall_performance_score"] - runner_up_score
    cost_driver = summary.sort_values("cost_share_pct", ascending=False).iloc[0]
    risk_driver = summary.sort_values(
        ["incident_day_rate_pct", "leak_day_rate_pct"], ascending=[False, False]
    ).iloc[0]
    lowest_confidence = (
        confidence_summary.sort_values("confidence_score", ascending=True).iloc[0]
        if not confidence_summary.empty
        else None
    )

    insights.append(
        {
            "kicker": "Best Overall",
            "title": f"{leader['system_display']} currently leads the operating score.",
            "value": f"{leader['overall_performance_score']:.1f}",
            "copy": (
                f"It leads the current {decision_mode.lower()} model by {lead_margin:.1f} points over the nearest alternative."
            ),
        }
    )
    insights.append(
        {
            "kicker": "Cost Pressure",
            "title": f"{cost_driver['system_display']} carries the largest cost load.",
            "value": f"{cost_driver['cost_share_pct']:.1f}%",
            "copy": "This system accounts for the largest share of estimated operating cost in the current view.",
        }
    )
    insights.append(
        {
            "kicker": "Risk Concentration",
            "title": f"{risk_driver['system_display']} has the heaviest risk exposure.",
            "value": f"{risk_driver['incident_day_rate_pct']:.1f}% incident-day rate",
            "copy": (
                f"It also posts a {risk_driver['leak_day_rate_pct']:.1f}% leak-day rate, making it the first "
                "system to review for reliability improvements."
            ),
        }
    )
    if lowest_confidence is not None:
        insights.append(
            {
                "kicker": "Confidence",
                "title": f"{lowest_confidence['system_display']} needs extra caution in cross-system comparisons.",
                "value": f"{lowest_confidence['confidence_score']:.1f}",
                "copy": lowest_confidence["warning_summary"].capitalize() + ".",
            }
        )

    if not opportunities.empty:
        top_opportunity = opportunities.sort_values("potential_cost_savings", ascending=False).iloc[0]
        insights.append(
            {
                "kicker": "Savings Potential",
                "title": f"{top_opportunity['system_display']} has the largest visible optimization opportunity.",
                "value": format_currency(top_opportunity["potential_cost_savings"], 2),
                "copy": (
                    "Estimated savings are based on closing the gap to the best peer resource intensity "
                    "inside the filtered dataset."
                ),
            }
        )

    if not outcome_context.has_yield:
        outcome_card = {
            "kicker": "Outcome Readiness",
            "title": "The dataset is operations-rich but outcome-poor.",
            "value": "Yield unavailable",
            "copy": (
                "Add harvest quantity or yield measurements to unlock cost-per-kg, water-per-kg, and true "
                "production optimization."
            ),
        }
        if len(insights) >= 4:
            insights[3] = outcome_card
        else:
            insights.append(outcome_card)

    if comparison_context and comparison_context.get("applied_basis") == COMPARISON_BASIS_OPTIONS[0]:
        insights.append(
            {
                "kicker": "Comparison Basis",
                "title": "Full-window comparison is active.",
                "value": "Seasonality risk",
                "copy": comparison_context["basis_note"],
            }
        )

    return insights[:5]


def build_recommendations(
    summary: pd.DataFrame,
    opportunities: pd.DataFrame,
    outcome_context: OutcomeContext,
    decision_mode: str,
    confidence_summary: pd.DataFrame,
    comparison_context: dict[str, object] | None,
    explainability: pd.DataFrame,
) -> list[str]:
    if summary.empty:
        return []

    recommendations: list[str] = []
    cost_heavy = summary.sort_values("estimated_cost_per_100_plants", ascending=False).iloc[0]
    risk_heavy = summary.sort_values(
        ["incident_day_rate_pct", "leak_day_rate_pct"], ascending=[False, False]
    ).iloc[0]
    stable_leader = summary.sort_values("daily_water_volatility_pct", ascending=True).iloc[0]

    if decision_mode == "Cost Minimization":
        recommendations.append(
            f"Reduce resource waste in {cost_heavy['system_display']} first because it carries the highest estimated cost intensity per 100 plants."
        )
        recommendations.append(
            f"Keep {stable_leader['system_display']} as the near-term operating benchmark because it combines tighter control with lower volatility."
        )
    elif decision_mode == "Risk Reduction":
        recommendations.append(
            f"Address reliability in {risk_heavy['system_display']} first because it leads the current view on both incident-day and leak-day exposure."
        )
        recommendations.append(
            f"Use {stable_leader['system_display']} as the safer reference point for process stability while risk controls are tightened elsewhere."
        )
    elif decision_mode == "Sustainability":
        water_heavy = summary.sort_values("water_per_100_plants_l", ascending=False).iloc[0]
        nutrient_heavy = summary.sort_values("nutrient_per_100_plants_ml", ascending=False).iloc[0]
        recommendations.append(
            f"Reduce water intensity in {water_heavy['system_display']} first because it is the most resource-heavy system in the current sustainability lens."
        )
        recommendations.append(
            f"Target nutrient waste in {nutrient_heavy['system_display']} to improve sustainability without changing system scale."
        )
    else:
        recommendations.append(
            f"Prioritize {cost_heavy['system_display']} for efficiency work because it has the highest estimated cost intensity per 100 plants."
        )
        recommendations.append(
            f"Address reliability in {risk_heavy['system_display']} first because it leads the filtered view on incident-day and leak-day exposure."
        )
        recommendations.append(
            f"Use {stable_leader['system_display']} as the current operating benchmark for water stability and day-to-day control."
        )

    if not opportunities.empty:
        savings_row = opportunities.sort_values("potential_cost_savings", ascending=False).iloc[0]
        recommendations.append(
            f"The clearest near-term savings sit in {savings_row['system_display']}; matching best-peer input intensity could save about {format_currency(savings_row['potential_cost_savings'], 2)} in the selected period."
        )

    if not explainability.empty:
        weakest_system = explainability.sort_values("overall_performance_score", ascending=True).iloc[0]
        recommendations.append(
            f"{weakest_system['system_display']} needs the closest management attention because it is most affected by {weakest_system['weakest_driver'].lower()}."
        )

    if comparison_context and comparison_context.get("applied_basis") == COMPARISON_BASIS_OPTIONS[0] and comparison_context.get(
        "overlap_available"
    ):
        recommendations.append(
            "Use the overlapping comparison window before making strong system-level claims, because the full-date view still mixes different seasonal windows."
        )

    if not confidence_summary.empty:
        lowest_confidence = confidence_summary.sort_values("confidence_score", ascending=True).iloc[0]
        recommendations.append(
            f"Treat {lowest_confidence['system_display']} cautiously in executive conclusions because {lowest_confidence['warning_summary']}."
        )

    if not outcome_context.has_yield:
        recommendations.append(
            "Capture harvest or yield outputs in future cycles so the score can move from operational proxy mode to true production economics."
        )

    return recommendations[:5]
