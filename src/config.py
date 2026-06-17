import logging
import os
import re
import json
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[1]

logging.basicConfig(
    level=logging.INFO,
    format=(
        "%(asctime)s | "
        "%(levelname)s | "
        "%(name)s | "
        "%(funcName)s | "
        "%(message)s"
    ),
)

LOGGER = logging.getLogger("school_census")

DATASET_URL = os.getenv("DATASET_URL")
DATASET_NAME = os.getenv("DATASET_NAME")
DATA_FILE_DIR = os.getenv("DATA_FILE_DIR")

SELECTED_FILE_KEYWORDS = [
    re.sub(
        r"_\d{4}$",
        "",
        keyword.strip(),
        flags=re.IGNORECASE,
    ).upper()
    for keyword in os.getenv(
        "SELECTED_FILE_KEYWORDS",
        ""
    ).split(",")
]

DATA_DIR = PROJECT_ROOT / "data"
LANDING_DIR = DATA_DIR / "landing"
RAW_DIR = DATA_DIR / "raw"
SQL_DIR = PROJECT_ROOT / "sql"

DATABASE_URL = os.getenv("DATABASE_URL")
DATABASE_STAGING_SCHEMA = "staging"
DATABASE_ANALYTICS_SCHEMA = "analytics"

ANALYTICS_TABLE_MAPPINGS = json.loads(
    (
        PROJECT_ROOT
        / "config"
        / "analytics_table_mappings.json"
    ).read_text(encoding="utf-8")
)


def find_existing_zip(year: int) -> Path | None:
    """
    Search for an existing School Census ZIP file for a given year.

    Args:
        year:
            School Census reference year.

    Returns:
        Path:
            Path to the existing ZIP file when found.

        None:
            Returned when no ZIP file exists for the
            requested year.
    """

    matches = list(
        RAW_DIR.glob(f"{DATASET_NAME}_{year}*.zip")
    )

    if matches:
        LOGGER.info("ZIP file already exists for year %s: %s", year, matches[0])
        return matches[0]

    LOGGER.debug("No ZIP file found for year %s.", year)

    return None


def build_census_urls(year: int) -> list[str]:
    """
    Build all possible download URLs for a School Census ZIP file.

    The INEP portal may expose files using slightly different
    naming conventions depending on the publication year.
    This function generates all supported URL patterns that
    will be attempted during the download step.

    Args:
        year:
            School Census reference year.

    Returns:
        list[str]:
            List of candidate URLs for the requested year.

    Raises:
        ValueError:
            Raised when the requested year is earlier than
            the first available School Census dataset.
    """

    if year < 1995:
        raise ValueError(
            f"School Census data is not available for years before 1995. "
            f"Received: {year}"
        )

    base_url = f"{DATASET_URL}/{DATASET_NAME}_{year}"

    urls = [
        f"{base_url}.zip",
        f"{base_url}_.zip",
    ]

    LOGGER.info("Built %s possible download URLs for year %s.", len(urls), year)

    return urls