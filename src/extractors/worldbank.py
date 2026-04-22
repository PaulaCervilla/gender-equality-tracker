"""World Bank API client.

Fetches gender-related indicators across all countries via the public
World Bank Indicators API (no authentication required).

Docs: https://datahelpdesk.worldbank.org/knowledgebase/articles/889392
"""
from __future__ import annotations

import logging

import pandas as pd
from tqdm import tqdm

import config

from .http_client import http_get

log = logging.getLogger(__name__)


def fetch_indicator(indicator_code: str) -> pd.DataFrame:
    """Fetch a single World Bank indicator for all countries.

    Returns a long-format DataFrame with columns:
    ``country``, ``country_code``, ``year``, ``value``, ``indicator``.
    """
    url = f"{config.WORLDBANK_BASE_URL}/country/all/indicator/{indicator_code}"
    params = {
        "format": "json",
        "date": config.WORLDBANK_DATE_RANGE,
        "per_page": config.WORLDBANK_PER_PAGE,
    }
    payload = http_get(url, params=params).json()

    if not isinstance(payload, list) or len(payload) < 2 or payload[1] is None:
        log.warning("No data returned for indicator %s", indicator_code)
        return pd.DataFrame(
            columns=["country", "country_code", "year", "value", "indicator"]
        )

    records = payload[1]
    rows = [
        {
            "country": r["country"]["value"],
            "country_code": r["countryiso3code"] or r["country"]["id"],
            "year": int(r["date"]),
            "value": r["value"],
            "indicator": indicator_code,
        }
        for r in records
        if r.get("value") is not None
    ]
    return pd.DataFrame(rows)


def fetch_all_indicators(
    indicators: dict[str, str] | None = None,
) -> pd.DataFrame:
    """Fetch every configured indicator and return a single long DataFrame.

    The returned frame has an additional ``indicator_name`` column with the
    human-friendly name from :data:`config.WORLDBANK_INDICATORS`.
    """
    indicators = indicators or config.WORLDBANK_INDICATORS
    frames: list[pd.DataFrame] = []
    for code, name in tqdm(indicators.items(), desc="World Bank indicators"):
        df = fetch_indicator(code)
        df["indicator_name"] = name
        frames.append(df)
        log.info("Fetched %d rows for %s (%s)", len(df), name, code)

    if not frames:
        return pd.DataFrame()

    combined = pd.concat(frames, ignore_index=True)
    log.info("Total World Bank records: %d", len(combined))
    return combined
