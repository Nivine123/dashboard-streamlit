from __future__ import annotations

from typing import Iterable

import pandas as pd

from .config import TRUE_VALUES


def split_crop_types(value: object) -> list[str]:
    if pd.isna(value):
        return ["Unknown"]

    items: list[str] = []
    for raw_item in str(value).split(","):
        item = raw_item.strip()
        if not item:
            continue
        normalized = item.title() if item.islower() else item
        if normalized not in items:
            items.append(normalized)
    return items or ["Unknown"]


def parse_issue_categories(value: object) -> list[str]:
    if pd.isna(value):
        return []

    items: list[str] = []
    for raw_item in str(value).split(";"):
        item = raw_item.strip()
        if not item or item == "No Issue Recorded":
            continue
        if item not in items:
            items.append(item)
    return items


def is_true(value: object) -> bool:
    if pd.isna(value):
        return False
    return str(value).strip().lower() in TRUE_VALUES


def any_match(values: Iterable[str], selected: set[str]) -> bool:
    return bool(set(values) & selected)


def safe_divide(numerator: float, denominator: float) -> float:
    if denominator in (0, 0.0) or pd.isna(denominator):
        return 0.0
    return float(numerator) / float(denominator)


def normalize_series(series: pd.Series, higher_is_better: bool) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce")
    minimum = values.min()
    maximum = values.max()
    if values.empty or pd.isna(minimum) or pd.isna(maximum) or minimum == maximum:
        return pd.Series([100.0] * len(values), index=values.index, dtype=float)

    if higher_is_better:
        normalized = (values - minimum) / (maximum - minimum)
    else:
        normalized = (maximum - values) / (maximum - minimum)

    return normalized.fillna(0.0) * 100


def coefficient_of_variation_pct(series: pd.Series) -> float:
    values = pd.to_numeric(series, errors="coerce").dropna()
    if values.empty:
        return 0.0
    mean_value = values.mean()
    if mean_value == 0:
        return 0.0
    return safe_divide(values.std(ddof=0), mean_value) * 100


def format_date(value) -> str:
    if pd.isna(value):
        return "Unknown"
    if hasattr(value, "strftime"):
        return value.strftime("%b %d, %Y").replace(" 0", " ")
    return str(value)


def format_currency(value: float, decimals: int = 0) -> str:
    return f"${value:,.{decimals}f}"


def format_number(value: float, decimals: int = 1) -> str:
    return f"{value:,.{decimals}f}"

