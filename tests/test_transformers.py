"""Tests for transformer modules."""
from __future__ import annotations

import pandas as pd

from src.transformers import cleaner, gender_index, nlp_analyzer


def _sample_long():
    return pd.DataFrame(
        [
            ("United States", "USA", 2022, 56.7, "SL.TLF.CACT.FE.ZS",
             "labor_force_participation_female"),
            ("United States", "USA", 2022, 67.5, "SL.TLF.CACT.MA.ZS",
             "labor_force_participation_male"),
            ("United States", "USA", 2022, 28.0, "SG.GEN.PARL.ZS",
             "women_in_parliament"),
            ("Spain", "ESP", 2022, 53.1, "SL.TLF.CACT.FE.ZS",
             "labor_force_participation_female"),
            ("Spain", "ESP", 2022, 63.0, "SL.TLF.CACT.MA.ZS",
             "labor_force_participation_male"),
            ("Spain", "ESP", 2022, 44.0, "SG.GEN.PARL.ZS",
             "women_in_parliament"),
            # An aggregate region that should be filtered out:
            ("World", "WLD", 2022, 50.0, "SL.TLF.CACT.FE.ZS",
             "labor_force_participation_female"),
        ],
        columns=["country", "country_code", "year", "value", "indicator", "indicator_name"],
    )


def test_filter_to_countries_drops_aggregates():
    df = cleaner.filter_to_countries(_sample_long())
    assert "WLD" not in df["country_code"].unique()
    assert {"USA", "ESP"} <= set(df["country_code"].unique())


def test_to_wide_indicator_table():
    long_df = cleaner.filter_to_countries(_sample_long())
    wide = cleaner.to_wide_indicator_table(long_df)
    assert {"labor_force_participation_female",
            "labor_force_participation_male",
            "women_in_parliament"} <= set(wide.columns)
    usa = wide[wide["country_code"] == "USA"].iloc[0]
    assert usa["labor_force_participation_female"] == 56.7


def test_compute_index_produces_score_in_range():
    long_df = cleaner.filter_to_countries(_sample_long())
    wide = cleaner.to_wide_indicator_table(long_df)
    snapshot = cleaner.latest_snapshot(wide)
    scored = gender_index.compute_index(snapshot)
    assert "gender_equality_score" in scored.columns
    scores = scored["gender_equality_score"].dropna()
    assert (scores.between(0, 100)).all()


def test_analyze_headlines_assigns_labels():
    df = pd.DataFrame(
        {
            "title": [
                "Wonderful progress on gender equality",
                "Wage gap remains catastrophic",
                "Report published today",
            ],
            "published": [pd.Timestamp.utcnow()] * 3,
        }
    )
    out = nlp_analyzer.analyze_headlines(df)
    assert "sentiment_compound" in out.columns
    assert out["sentiment_label"].isin(["positive", "neutral", "negative"]).all()
