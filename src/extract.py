from pathlib import Path
from zipfile import ZipFile

import re
import certifi
import requests
import urllib3
import time

from requests import Response
from requests.exceptions import SSLError

from src.config import (
    find_existing_zip,
    build_census_urls,
    RAW_DIR,
    LANDING_DIR,
    DATASET_NAME,
    DATA_FILE_PATH,
    SELECTED_FILE_KEYWORDS,
)


def get_with_ssl_retry(url: str) -> Response:
    """
    Performs an HTTPS request using certificate validation first.
    If SSL validation fails, retries without certificate verification.
    """

    try:
        return requests.get(
            url,
            stream=True,
            timeout=120,
            verify=certifi.where(),
        )

    except SSLError:
        print(
            "SSL verification failed. "
            "Retrying without certificate verification..."
        )

        urllib3.disable_warnings(
            urllib3.exceptions.InsecureRequestWarning
        )

        return requests.get(
            url,
            stream=True,
            timeout=120,
            verify=False,
        )


def download_census_zip(year: int) -> Path:
    """
    Downloads the School Census ZIP file for a given year.
    """

    existing_zip = find_existing_zip(year)

    if existing_zip:
        raise FileExistsError(
            f"School Census ZIP for year {year} already exists: "
            f"{existing_zip}"
        )

    target_dir = RAW_DIR / DATASET_NAME
    target_dir.mkdir(parents=True, exist_ok=True)

    print(f"Downloading INEP School Census ZIP for {year}...")

    errors = []

    for zip_url in build_census_urls(year):
        zip_path = target_dir / Path(zip_url).name

        try:
            print(f"Trying URL: {zip_url}")

            with get_with_ssl_retry(zip_url) as response:
                response.raise_for_status()

                with zip_path.open("wb") as file:
                    for chunk in response.iter_content(
                        chunk_size=1024 * 1024
                    ):
                        if chunk:
                            file.write(chunk)

            print(f"Downloaded ZIP to: {zip_path}")

            return zip_path

        except requests.RequestException as error:
            errors.append(f"{zip_url} -> {error}")

            print(
                f"Failed to download from {zip_url}: {error}"
            )

            if zip_path.exists():
                zip_path.unlink()

    raise FileNotFoundError(
        f"Could not download School Census ZIP for year {year}. "
        f"Tried {len(errors)} URLs.\n"
        + "\n".join(errors)
    )


def should_extract_file(target_path: Path, filename: str) -> bool:
    """
    Checks whether the file should be extracted.
    """

    normalized_name = re.sub(
        r"_\d{4}(?=\.csv$)",
        "",
        filename,
        flags=re.IGNORECASE,
    ).upper()

    return (
        normalized_name.endswith(".CSV")
        and any(
            keyword in normalized_name
            for keyword in SELECTED_FILE_KEYWORDS
        )
    )


def find_data_directory(root_path: Path) -> Path:
    for path in root_path.rglob("*"):
        if path.is_dir() and path.name.lower() == DATA_FILE_PATH:
            return path

    raise FileNotFoundError(
        f"Could not find a 'dados' directory under {root_path}"
    )


def extract_selected_csv_files(
    zip_path: Path,
    year: int,
) -> list[Path]:
    """
    Extracts only the selected CSV files from the ZIP.
    """

    LANDING_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    extracted_files = []

    with ZipFile(zip_path, "r") as zip_file:
        for member in zip_file.namelist():
            path = Path(member)
            filename = path.name

            if DATA_FILE_PATH not in [part.lower() for part in path.parts]:
                continue

            table_name = re.sub(
                r"^tabela_|_\d{4}\.csv$",
                "",
                filename,
                flags=re.IGNORECASE,
            ).lower()

            ingestion_timestamp = int(time.time())
            target_path = LANDING_DIR / DATASET_NAME / table_name / str(year) / f"{table_name}_{ingestion_timestamp}.csv"

            if not should_extract_file(target_path, filename):
                continue

            target_path.parent.mkdir(parents=True, exist_ok=True)

            print(f"Extracting {filename}...")

            with zip_file.open(member) as source:
                with target_path.open("wb") as target:
                    target.write(source.read())
            
            extracted_files.append(target_path)

    if not extracted_files:
        raise FileNotFoundError(
            "No selected CSV files were found in the ZIP."
        )

    return extracted_files


def extract_census_data(year: int) -> list[Path]:
    """
    Executes the extraction pipeline.
    """

    try:
        zip_path = download_census_zip(year)
        return extract_selected_csv_files(zip_path, year)

    except Exception as error:
        raise RuntimeError(
            f"Error extracting census data for year {year}"
        ) from error