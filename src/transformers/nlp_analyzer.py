"""Sentiment analysis on news headlines using VADER."""
from __future__ import annotations

import logging

import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

log = logging.getLogger(__name__)


def analyze_headlines(news_df: pd.DataFrame) -> pd.DataFrame:
    """Add ``sentiment_compound`` and ``sentiment_label`` columns.

    The compound score is in [-1, 1]. We bucket it into negative / neutral /
    positive at the conventional ±0.05 thresholds.
    """
    if news_df.empty:
        return news_df.assign(sentiment_compound=[], sentiment_label=[])

    analyzer = SentimentIntensityAnalyzer()
    df = news_df.copy()
    scores = df["title"].fillna("").apply(analyzer.polarity_scores)
    df["sentiment_compound"] = scores.apply(lambda d: d["compound"])
    df["sentiment_label"] = pd.cut(
        df["sentiment_compound"],
        bins=[-1.01, -0.05, 0.05, 1.01],
        labels=["negative", "neutral", "positive"],
    )
    log.info(
        "Sentiment distribution: %s",
        df["sentiment_label"].value_counts().to_dict(),
    )
    return df
