"""News scraper for gender-equality-related headlines.

Uses Google News RSS feeds (structured XML) and BeautifulSoup with the
``lxml-xml`` parser. RSS is more stable than scraping HTML pages.
"""
from __future__ import annotations

import logging
from datetime import datetime
from email.utils import parsedate_to_datetime
from urllib.parse import quote_plus

import pandas as pd
from bs4 import BeautifulSoup
from tqdm import tqdm

import config

from .http_client import http_get

log = logging.getLogger(__name__)


def _parse_pub_date(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        return parsedate_to_datetime(raw)
    except (TypeError, ValueError):
        return None


def fetch_news_for_query(query: str) -> pd.DataFrame:
    """Return DataFrame: title, link, published, source, query."""
    url = config.GOOGLE_NEWS_RSS.format(query=quote_plus(query))
    resp = http_get(url)
    soup = BeautifulSoup(resp.content, "lxml-xml")

    rows = []
    for item in soup.find_all("item"):
        title = item.title.text if item.title else ""
        link = item.link.text if item.link else ""
        pub = _parse_pub_date(item.pubDate.text if item.pubDate else None)
        source = item.source.text if item.source else ""
        rows.append(
            {
                "title": title,
                "link": link,
                "published": pub,
                "source": source,
                "query": query,
            }
        )
    log.info("Fetched %d headlines for query=%r", len(rows), query)
    return pd.DataFrame(rows)


def fetch_all_news(queries: list[str] | None = None) -> pd.DataFrame:
    """Fetch headlines for every configured query and dedupe by title."""
    queries = queries or config.NEWS_QUERIES
    frames = [fetch_news_for_query(q) for q in tqdm(queries, desc="News queries")]
    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames, ignore_index=True)
    df = df.drop_duplicates(subset=["title"]).reset_index(drop=True)
    log.info("Total unique headlines: %d", len(df))
    return df
