"""Clean and reshape raw extracted data."""
from __future__ import annotations

import logging

import pandas as pd
import pycountry

log = logging.getLogger(__name__)


# World Bank "country" results include aggregate regions (e.g. "World",
# "Euro area"). Filter them out using pycountry's official ISO 3166 list.
_VALID_ISO3 = {c.alpha_3 for c in pycountry.countries}


def filter_to_countries(df: pd.DataFrame) -> pd.DataFrame:
    """Keep only rows whose country_code is a real ISO-3166 alpha-3 code."""
    if df.empty:
        return df
    return df[df["country_code"].isin(_VALID_ISO3)].copy()


def to_wide_indicator_table(long_df: pd.DataFrame) -> pd.DataFrame:
    """Pivot World Bank long format to wide: one row per (country, year)."""
    if long_df.empty:
        return long_df
    wide = long_df.pivot_table(
        index=["country", "country_code", "year"],
        columns="indicator_name",
        values="value",
        aggfunc="first",
    ).reset_index()
    wide.columns.name = None
    return wide


def latest_per_country(wide_df: pd.DataFrame, indicator: str) -> pd.DataFrame:
    """Return the most recent non-null value per country for one indicator."""
    if wide_df.empty or indicator not in wide_df.columns:
        return pd.DataFrame(columns=["country", "country_code", "year", indicator])
    sub = wide_df.dropna(subset=[indicator]).sort_values("year")
    return (
        sub.groupby("country_code", as_index=False)
        .tail(1)
        .reset_index(drop=True)[["country", "country_code", "year", indicator]]
    )


def latest_snapshot(wide_df: pd.DataFrame) -> pd.DataFrame:
    """Most recent value for every indicator per country (independent latest)."""
    if wide_df.empty:
        return wide_df

    indicator_cols = [
        c for c in wide_df.columns if c not in {"country", "country_code", "year"}
    ]
    snapshot = (
        wide_df.groupby("country_code", as_index=False)
        .agg(country=("country", "first"))
    )
    for col in indicator_cols:
        latest = latest_per_country(wide_df, col).drop(columns=["country", "year"])
        snapshot = snapshot.merge(latest, on="country_code", how="left")

    log.info("Built latest snapshot: %d countries × %d indicators",
             len(snapshot), len(indicator_cols))
    return snapshot
