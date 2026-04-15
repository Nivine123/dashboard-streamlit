from __future__ import annotations

from datetime import timedelta

import pandas as pd
import streamlit as st

from .config import (
    AREA_CANDIDATES,
    COMPARISON_BASIS_OPTIONS,
    DATA_FILE,
    QUALITY_CANDIDATES,
    SYSTEM_DISPLAY_NAMES,
    YIELD_CANDIDATES,
)
from .utils import any_match, is_true, parse_issue_categories, split_crop_types


NUMERIC_COLUMNS = [
    "water_use_l",
    "nutrient_total_ml",
    "plant_count",
    "age_days",
    *YIELD_CANDIDATES,
    *AREA_CANDIDATES,
    *QUALITY_CANDIDATES,
]


@st.cache_data(show_spinner=False)
def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_FILE)

    for column in NUMERIC_COLUMNS:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")

    df["observation_date_dt"] = pd.to_datetime(df["observation_date"], errors="coerce")
    df["date_only"] = df["observation_date_dt"].dt.date
    df["water_use_l"] = pd.to_numeric(df.get("water_use_l"), errors="coerce").fillna(0.0)
    df["nutrient_total_ml"] = pd.to_numeric(df.get("nutrient_total_ml"), errors="coerce").fillna(0.0)

    df["issue_flag_bool"] = df["issue_flag"].apply(is_true)
    df["leak_flag_bool"] = df["leak_flag"].apply(is_true)
    df["crop_type_list"] = df["crop_types"].apply(split_crop_types)
    df["issue_category_list"] = df["problem_categories"].apply(parse_issue_categories)
    df["system_label"] = df["system"].fillna("Unknown").replace("", "Unknown")
    df["system_display"] = df["system_label"].map(SYSTEM_DISPLAY_NAMES).fillna(df["system_label"])
    df["system_type"] = df["system_type"].fillna("Unknown").replace("", "Unknown")
    df["leak_severity_label"] = df["leak_severity"].fillna("Unknown").replace("", "Unknown")
    df["quality_label"] = df["data_quality_status"].fillna("Unknown").replace("", "Unknown")

    positive_plant_counts = pd.to_numeric(df.get("plant_count"), errors="coerce")
    positive_plant_counts = positive_plant_counts.where(positive_plant_counts > 0)
    system_median_plants = positive_plant_counts.groupby(df["system_label"]).transform("median")
    overall_median_plants = positive_plant_counts.median()
    fallback_plant_count = overall_median_plants if pd.notna(overall_median_plants) else 1.0

    df["plant_count_clean"] = positive_plant_counts
    df["plant_count_imputed"] = positive_plant_counts.isna()
    df["plant_count_filled"] = (
        positive_plant_counts.fillna(system_median_plants).fillna(fallback_plant_count)
    )

    return df.sort_values(["observation_date_dt", "system_display"]).reset_index(drop=True)


def build_filter_options(df: pd.DataFrame) -> dict[str, list[str]]:
    return {
        "system_types": sorted(
            value for value in df["system_type"].dropna().unique() if str(value).strip()
        ),
        "system_names": sorted(
            value for value in df["system_display"].dropna().unique() if str(value).strip()
        ),
        "crop_types": sorted(
            {crop for crop_list in df["crop_type_list"] for crop in crop_list if crop}
        ),
    }


def apply_filters(df: pd.DataFrame, filters: dict[str, object]) -> pd.DataFrame:
    filtered_df = df[
        df["date_only"].between(filters["start_date"], filters["end_date"], inclusive="both")
    ].copy()

    if filters["system_types"]:
        filtered_df = filtered_df[filtered_df["system_type"].isin(filters["system_types"])]
    else:
        filtered_df = filtered_df.iloc[0:0]

    if filters["system_names"]:
        filtered_df = filtered_df[filtered_df["system_display"].isin(filters["system_names"])]
    else:
        filtered_df = filtered_df.iloc[0:0]

    if filters["crop_types"]:
        selected_crop_set = set(filters["crop_types"])
        filtered_df = filtered_df[
            filtered_df["crop_type_list"].apply(lambda values: any_match(values, selected_crop_set))
        ]
    else:
        filtered_df = filtered_df.iloc[0:0]

    return filtered_df.reset_index(drop=True)


def comparison_window(
    df: pd.DataFrame, filters: dict[str, object]
) -> tuple[pd.DataFrame, object, object, bool]:
    window_days = (filters["end_date"] - filters["start_date"]).days + 1
    previous_end = filters["start_date"] - timedelta(days=1)
    previous_start = previous_end - timedelta(days=window_days - 1)
    minimum_date = df["date_only"].dropna().min()

    if previous_end < minimum_date:
        return df.iloc[0:0].copy(), previous_start, previous_end, False

    previous_filters = {**filters, "start_date": previous_start, "end_date": previous_end}
    return apply_filters(df, previous_filters), previous_start, previous_end, True


def apply_comparison_basis(
    filtered_df: pd.DataFrame, comparison_basis: str
) -> tuple[pd.DataFrame, dict[str, object]]:
    if filtered_df.empty:
        empty_context = {
            "comparison_basis": comparison_basis,
            "applied_basis": comparison_basis,
            "selected_start": None,
            "selected_end": None,
            "selected_days": 0,
            "overlap_start": None,
            "overlap_end": None,
            "overlap_days": 0,
            "overlap_available": False,
            "overlap_applied": False,
            "basis_note": "No filtered rows are available for comparison.",
            "basis_warning": "",
            "coverage": pd.DataFrame(),
        }
        return filtered_df, empty_context

    coverage = (
        filtered_df.dropna(subset=["date_only"])
        .groupby("system_display", as_index=False)
        .agg(
            system_start=("date_only", "min"),
            system_end=("date_only", "max"),
            active_days=("date_only", "nunique"),
            rows=("system_display", "size"),
        )
    )

    selected_start = filtered_df["date_only"].dropna().min()
    selected_end = filtered_df["date_only"].dropna().max()
    selected_days = (selected_end - selected_start).days + 1 if selected_start and selected_end else 0
    overlap_start = coverage["system_start"].max() if not coverage.empty else None
    overlap_end = coverage["system_end"].min() if not coverage.empty else None
    overlap_available = bool(
        overlap_start is not None and overlap_end is not None and overlap_start <= overlap_end
    )
    overlap_days = (overlap_end - overlap_start).days + 1 if overlap_available else 0

    if comparison_basis == COMPARISON_BASIS_OPTIONS[1] and overlap_available:
        adjusted_df = filtered_df[
            filtered_df["date_only"].between(overlap_start, overlap_end, inclusive="both")
        ].copy()
        applied_basis = COMPARISON_BASIS_OPTIONS[1]
        overlap_applied = True
        basis_note = (
            f"Only the shared date window from {overlap_start} to {overlap_end} is used so system "
            "comparisons are more fair across seasonality and timing."
        )
        basis_warning = ""
    else:
        adjusted_df = filtered_df.copy()
        applied_basis = COMPARISON_BASIS_OPTIONS[0]
        overlap_applied = False
        if comparison_basis == COMPARISON_BASIS_OPTIONS[1] and not overlap_available:
            basis_note = "No usable overlapping window exists across the selected systems, so the full filtered dataset is shown."
            basis_warning = "Overlap window unavailable"
        elif overlap_available and selected_days > overlap_days:
            basis_note = (
                f"The full filtered dataset is shown. A fairer shared window is also available from "
                f"{overlap_start} to {overlap_end}."
            )
            basis_warning = "Cross-system timing differs"
        else:
            basis_note = "The full filtered dataset is shown."
            basis_warning = ""

    context = {
        "comparison_basis": comparison_basis,
        "applied_basis": applied_basis,
        "selected_start": selected_start,
        "selected_end": selected_end,
        "selected_days": selected_days,
        "overlap_start": overlap_start,
        "overlap_end": overlap_end,
        "overlap_days": overlap_days,
        "overlap_available": overlap_available,
        "overlap_applied": overlap_applied,
        "basis_note": basis_note,
        "basis_warning": basis_warning,
        "coverage": coverage,
    }
    return adjusted_df.reset_index(drop=True), context
