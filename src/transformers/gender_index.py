"""Composite Gender Equality Score.

Builds intermediate component scores from the cleaned snapshot, normalizes
each to [0, 1] using min-max scaling, then computes a weighted average
based on :data:`config.GENDER_INDEX_COMPONENTS`.
"""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd

import config

log = logging.getLogger(__name__)


def _col(df: pd.DataFrame, name: str) -> pd.Series:
    """Return df[name] or an all-NaN series if the column is missing."""
    if name in df.columns:
        return df[name]
    return pd.Series(np.nan, index=df.index, name=name)


def _safe_ratio(num: pd.Series, denom: pd.Series) -> pd.Series:
    """Element-wise ratio, capped at 1.0 (so females-above-males = perfect)."""
    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = np.where(denom > 0, num / denom, np.nan)
    return pd.Series(ratio, index=num.index).clip(upper=1.0)


def _minmax(series: pd.Series, higher_is_better: bool) -> pd.Series:
    """Scale to [0, 1]; invert if lower values indicate more equality."""
    s = series.astype(float)
    lo, hi = s.min(skipna=True), s.max(skipna=True)
    if pd.isna(lo) or pd.isna(hi) or hi == lo:
        return pd.Series(np.nan, index=s.index)
    scaled = (s - lo) / (hi - lo)
    return scaled if higher_is_better else 1 - scaled


def build_components(snapshot: pd.DataFrame) -> pd.DataFrame:
    """Add raw component columns (ratios / gaps) used by the index."""
    df = snapshot.copy()
    df["labor_force_ratio"] = _safe_ratio(
        _col(df, "labor_force_participation_female"),
        _col(df, "labor_force_participation_male"),
    )
    df["literacy_ratio"] = _safe_ratio(
        _col(df, "literacy_female"), _col(df, "literacy_male")
    )
    df["wage_workers_ratio"] = _safe_ratio(
        _col(df, "wage_workers_female"), _col(df, "wage_workers_male")
    )
    df["unemployment_gap"] = (
        _col(df, "unemployment_female") - _col(df, "unemployment_male")
    ).abs()
    # women_in_parliament & school_enrollment_gpi are passed through as-is
    return df


def compute_index(snapshot: pd.DataFrame) -> pd.DataFrame:
    """Return snapshot with extra ``gender_equality_score`` column (0-100)."""
    df = build_components(snapshot)

    weighted_sum = pd.Series(0.0, index=df.index)
    weight_total = pd.Series(0.0, index=df.index)

    for component, meta in config.GENDER_INDEX_COMPONENTS.items():
        if component not in df.columns:
            log.warning("Component %s missing from snapshot", component)
            continue
        scaled = _minmax(df[component], higher_is_better=meta["higher_is_better"])
        weight = meta["weight"]
        # only count weight where the country actually has the data
        mask = scaled.notna()
        weighted_sum = weighted_sum.add(scaled.fillna(0) * weight, fill_value=0)
        weight_total = weight_total.add(mask.astype(float) * weight, fill_value=0)

    score = (weighted_sum / weight_total.replace(0, np.nan)) * 100
    df["gender_equality_score"] = score.round(2)

    log.info(
        "Computed Gender Equality Score for %d countries (mean=%.1f)",
        df["gender_equality_score"].notna().sum(),
        df["gender_equality_score"].mean(),
    )
    return df
