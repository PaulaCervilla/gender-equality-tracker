"""End-to-end pipeline: extract → transform → load → visualize."""
from __future__ import annotations

import logging

from src.extractors import news_scraper, oecd, worldbank
from src.loaders import storage
from src.transformers import cleaner, gender_index, nlp_analyzer
from src.visualizations import dashboard


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )


def run() -> None:
    configure_logging()
    log = logging.getLogger("pipeline")

    log.info("=== Step 1/4: Extracting raw data ===")
    wb_long = worldbank.fetch_all_indicators()
    oecd_df = oecd.fetch_gender_wage_gap()
    news_df = news_scraper.fetch_all_news()

    log.info("=== Step 2/4: Transforming ===")
    wb_long = cleaner.filter_to_countries(wb_long)
    wb_wide = cleaner.to_wide_indicator_table(wb_long)
    snapshot = cleaner.latest_snapshot(wb_wide)
    snapshot = gender_index.compute_index(snapshot)
    news_df = nlp_analyzer.analyze_headlines(news_df)

    log.info("=== Step 3/4: Loading ===")
    storage.save_csv(wb_long, "worldbank_long")
    storage.save_csv(wb_wide, "worldbank_wide")
    storage.save_csv(snapshot, "country_snapshot")
    storage.save_csv(oecd_df, "oecd_wage_gap")
    storage.save_csv(news_df, "news_sentiment")
    storage.save_sqlite(
        {
            "worldbank_long": wb_long,
            "worldbank_wide": wb_wide,
            "country_snapshot": snapshot,
            "oecd_wage_gap": oecd_df,
            "news_sentiment": news_df,
        }
    )

    log.info("=== Step 4/4: Building dashboard ===")
    out = dashboard.build_dashboard(snapshot, wb_long, oecd_df, news_df)
    log.info("Done. Open %s in a browser.", out)


if __name__ == "__main__":
    run()
