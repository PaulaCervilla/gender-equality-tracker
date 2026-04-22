"""Tests for extractor modules — network calls are mocked."""
from __future__ import annotations

from unittest.mock import patch

import pandas as pd

from src.extractors import news_scraper, worldbank


_FAKE_WB_PAYLOAD = [
    {"page": 1, "pages": 1, "per_page": 100, "total": 2},
    [
        {
            "country": {"id": "US", "value": "United States"},
            "countryiso3code": "USA",
            "date": "2022",
            "value": 56.7,
            "indicator": {"id": "SL.TLF.CACT.FE.ZS"},
        },
        {
            "country": {"id": "ES", "value": "Spain"},
            "countryiso3code": "ESP",
            "date": "2022",
            "value": 53.1,
            "indicator": {"id": "SL.TLF.CACT.FE.ZS"},
        },
        {
            "country": {"id": "ES", "value": "Spain"},
            "countryiso3code": "ESP",
            "date": "2021",
            "value": None,  # should be filtered out
            "indicator": {"id": "SL.TLF.CACT.FE.ZS"},
        },
    ],
]


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload

    @property
    def content(self):
        return self._payload if isinstance(self._payload, bytes) else b""

    @property
    def text(self):
        return self._payload if isinstance(self._payload, str) else ""


def test_fetch_indicator_parses_payload():
    with patch("src.extractors.worldbank.http_get",
               return_value=_FakeResponse(_FAKE_WB_PAYLOAD)):
        df = worldbank.fetch_indicator("SL.TLF.CACT.FE.ZS")

    assert len(df) == 2  # null row filtered
    assert set(df["country_code"]) == {"USA", "ESP"}
    assert df["indicator"].unique().tolist() == ["SL.TLF.CACT.FE.ZS"]


def test_fetch_indicator_handles_empty():
    empty_payload = [{"message": "no data"}, None]
    with patch("src.extractors.worldbank.http_get",
               return_value=_FakeResponse(empty_payload)):
        df = worldbank.fetch_indicator("X.Y.Z")
    assert df.empty
    assert list(df.columns) == ["country", "country_code", "year", "value", "indicator"]


_FAKE_RSS = b"""<?xml version="1.0"?>
<rss version="2.0"><channel>
<item>
  <title>Gender pay gap narrows in 2025</title>
  <link>https://example.com/a</link>
  <pubDate>Tue, 21 Apr 2026 10:00:00 GMT</pubDate>
  <source>Example News</source>
</item>
<item>
  <title>Women leaders make headlines</title>
  <link>https://example.com/b</link>
  <pubDate>Mon, 20 Apr 2026 09:00:00 GMT</pubDate>
  <source>Other News</source>
</item>
</channel></rss>"""


def test_fetch_news_for_query_parses_rss():
    fake = _FakeResponse(_FAKE_RSS)
    with patch("src.extractors.news_scraper.http_get", return_value=fake):
        df = news_scraper.fetch_news_for_query("gender pay gap")

    assert len(df) == 2
    assert "Gender pay gap narrows" in df.iloc[0]["title"]
    assert pd.notna(df.iloc[0]["published"])
    assert df.iloc[0]["source"] == "Example News"
