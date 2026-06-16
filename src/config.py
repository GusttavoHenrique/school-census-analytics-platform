import re
import os

from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATASET_URL = os.getenv("DATASET_URL")
DATASET_NAME = os.getenv("DATASET_NAME")
DATA_FILE_PATH = os.getenv("DATA_FILE_PATH")
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

DATABASE_URL = os.getenv("DATABASE_URL")


def find_existing_zip(year: int) -> Path | None:
    """
    Verify if an especific zip file already exists.
    """

    matches = list(
        RAW_DIR.glob(f"{DATASET_NAME}_{year}*.zip")
    )

    if matches:
        print("A ZIP file already exists for the requested census year.")
        return matches[0]  
    
    return None


def build_census_urls(year: int) -> list[str]:
    """
    Build the possible url to file in data portal.
    """

    if year < 1995:
        raise ValueError(
            f"School Census data is not available for years before 1995. "
            f"Received: {year}"
        )

    base_url = (
        f"{DATASET_URL}/{DATASET_NAME}_{year}"
    )

    return [
        f"{base_url}.zip",
        f"{base_url}_.zip",
    ]