"""Configuration: API endpoints, indicator codes, and constants."""
from __future__ import annotations

from pathlib import Path

# --- Paths ---
ROOT_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "data"
OUTPUT_DIR = ROOT_DIR / "output"
DB_PATH = DATA_DIR / "gender_equality.db"

DATA_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# --- World Bank API ---
WORLDBANK_BASE_URL = "https://api.worldbank.org/v2"
WORLDBANK_DATE_RANGE = "2000:2023"
WORLDBANK_PER_PAGE = 20000  # one page = all data

# Indicator code -> human-friendly column name
WORLDBANK_INDICATORS: dict[str, str] = {
    "SL.TLF.CACT.FE.ZS": "labor_force_participation_female",
    "SL.TLF.CACT.MA.ZS": "labor_force_participation_male",
    "SG.GEN.PARL.ZS": "women_in_parliament",
    "SE.ADT.LITR.FE.ZS": "literacy_female",
    "SE.ADT.LITR.MA.ZS": "literacy_male",
    "SL.EMP.WORK.FE.ZS": "wage_workers_female",
    "SL.EMP.WORK.MA.ZS": "wage_workers_male",
    "SL.UEM.TOTL.FE.ZS": "unemployment_female",
    "SL.UEM.TOTL.MA.ZS": "unemployment_male",
    "SE.ENR.PRSC.FM.ZS": "school_enrollment_gpi",
    "SP.DYN.LE00.FE.IN": "life_expectancy_female",
    "SP.DYN.LE00.MA.IN": "life_expectancy_male",
}

# Indicators used in the composite Gender Equality Score and their weights.
# "higher_is_better" means a higher value indicates more equality.
GENDER_INDEX_COMPONENTS: dict[str, dict] = {
    "labor_force_ratio": {
        "weight": 0.25,
        "higher_is_better": True,
        "description": "Female / Male labor force participation ratio",
    },
    "women_in_parliament": {
        "weight": 0.20,
        "higher_is_better": True,
        "description": "% of parliamentary seats held by women",
    },
    "literacy_ratio": {
        "weight": 0.15,
        "higher_is_better": True,
        "description": "Female / Male literacy ratio",
    },
    "wage_workers_ratio": {
        "weight": 0.15,
        "higher_is_better": True,
        "description": "Female / Male wage worker ratio",
    },
    "unemployment_gap": {
        "weight": 0.10,
        "higher_is_better": False,  # Lower (closer to 0) gap = more equal
        "description": "Female unemployment minus male unemployment",
    },
    "school_enrollment_gpi": {
        "weight": 0.15,
        "higher_is_better": True,
        "description": "School enrollment gender parity index",
    },
}

# --- OECD ---
# OECD SDMX REST endpoint for the gender wage gap dataset.
OECD_GENDER_WAGE_GAP_URL = (
    "https://sdmx.oecd.org/public/rest/data/OECD.ELS.SAE,DSD_EARNINGS@GENDER_WAGE_GAP,"
    "/all?format=csvfilewithlabels&dimensionAtObservation=AllDimensions"
)

# --- News scraping ---
GOOGLE_NEWS_RSS = (
    "https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
)
NEWS_QUERIES: list[str] = [
    "gender pay gap",
    "women in leadership",
    "gender equality workplace",
    "feminism rights",
]

# --- HTTP ---
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3
USER_AGENT = (
    "gender-equality-tracker/1.0 (+https://github.com/example/gender-equality-tracker)"
)
