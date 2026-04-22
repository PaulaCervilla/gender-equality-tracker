"""Persist processed datasets to CSV and SQLite."""
from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

import pandas as pd

import config

log = logging.getLogger(__name__)


def save_csv(df: pd.DataFrame, name: str) -> Path:
    path = config.DATA_DIR / f"{name}.csv"
    df.to_csv(path, index=False)
    log.info("Wrote %s (%d rows)", path, len(df))
    return path


def save_sqlite(tables: dict[str, pd.DataFrame], db_path: Path | None = None) -> Path:
    db_path = db_path or config.DB_PATH
    with sqlite3.connect(db_path) as conn:
        for name, df in tables.items():
            df.to_sql(name, conn, if_exists="replace", index=False)
            log.info("Wrote SQLite table %s (%d rows)", name, len(df))
    return db_path
