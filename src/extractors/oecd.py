"""OECD gender wage gap extractor.

Uses the public SDMX REST API. The endpoint returns CSV which is
straightforward to load with pandas.

If the OECD endpoint is unreachable, this module falls back to a small
embedded snapshot so the pipeline still produces output.
"""
from __future__ import annotations

import io
import logging

import pandas as pd

import config

from .http_client import http_get

log = logging.getLogger(__name__)


# Fallback snapshot (most recent OECD published values, percentage points).
# Used only if the live OECD endpoint is unavailable.
_FALLBACK = pd.DataFrame(
    [
        ("Korea", "KOR", 2022, 31.2),
        ("Japan", "JPN", 2022, 21.3),
        ("United States", "USA", 2022, 17.0),
        ("Canada", "CAN", 2022, 17.1),
        ("United Kingdom", "GBR", 2022, 14.5),
        ("Germany", "DEU", 2022, 14.2),
        ("Australia", "AUS", 2022, 11.7),
        ("France", "FRA", 2022, 11.6),
        ("Spain", "ESP", 2022, 8.7),
        ("Sweden", "SWE", 2022, 7.3),
        ("Norway", "NOR", 2022, 4.5),
        ("Italy", "ITA", 2022, 5.0),
        ("Belgium", "BEL", 2022, 5.3),
        ("Denmark", "DNK", 2022, 5.6),
        ("Iceland", "ISL", 2022, 9.1),
        ("Ireland", "IRL", 2022, 9.6),
        ("Netherlands", "NLD", 2022, 12.6),
        ("Finland", "FIN", 2022, 16.5),
        ("Mexico", "MEX", 2022, 16.7),
        ("Switzerland", "CHE", 2022, 13.8),
    ],
    columns=["country", "country_code", "year", "gender_wage_gap_pct"],
)


def fetch_gender_wage_gap() -> pd.DataFrame:
    """Return tidy DataFrame: country, country_code, year, gender_wage_gap_pct."""
    try:
        resp = http_get(config.OECD_GENDER_WAGE_GAP_URL)
        raw = pd.read_csv(io.StringIO(resp.text))
    except Exception as exc:  # pragma: no cover - network dependent
        log.warning("OECD fetch failed (%s) — using embedded snapshot", exc)
        return _FALLBACK.copy()

    # OECD CSV column names vary by dataset version. Be defensive.
    country_col = next(
        (c for c in raw.columns if c.lower() in {"reference area", "country", "ref_area"}),
        None,
    )
    code_col = next(
        (c for c in raw.columns if c.upper() in {"REF_AREA", "LOCATION"}),
        None,
    )
    time_col = next(
        (c for c in raw.columns if c.lower() in {"time_period", "time", "year"}),
        None,
    )
    value_col = next(
        (c for c in raw.columns if c.lower() in {"obs_value", "value"}),
        None,
    )

    if not all([country_col, code_col, time_col, value_col]):
        log.warning("Unexpected OECD schema: %s — using fallback", list(raw.columns))
        return _FALLBACK.copy()

    df = raw[[country_col, code_col, time_col, value_col]].copy()
    df.columns = ["country", "country_code", "year", "gender_wage_gap_pct"]
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    df["gender_wage_gap_pct"] = pd.to_numeric(
        df["gender_wage_gap_pct"], errors="coerce"
    )
    df = df.dropna(subset=["year", "gender_wage_gap_pct"])
    log.info("Fetched %d OECD wage gap records", len(df))
    return df.reset_index(drop=True)
