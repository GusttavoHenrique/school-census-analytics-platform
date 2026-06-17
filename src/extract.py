from pathlib import Path
from zipfile import ZipFile

import certifi
import requests
import re
import time
import urllib3

from requests import Response
from requests.exceptions import SSLError

from src.config import (
    LOGGER,
    find_existing_zip,
    build_census_urls,
    RAW_DIR,
    LANDING_DIR,
    DATASET_NAME,
    DATA_FILE_DIR,
    SELECTED_FILE_KEYWORDS,
)
from src.utils import get_table_by_raw_file


def get_with_ssl_retry(url: str) -> Response:
    """
    Perform an HTTP GET request with SSL fallback support.

    The request is initially executed using certificate
    validation. If an SSL validation error occurs, the
    request is retried with certificate verification
    disabled.

    Args:
        url:
            Target URL to be requested.

    Returns:
        Response:
            HTTP response returned by the remote server.

    Raises:
        requests.RequestException:
            Raised when the request cannot be completed.
    """

    try:
        return requests.get(
            url,
            stream=True,
            timeout=120,
            verify=certifi.where(),
        )

    except SSLError:
        LOGGER.warning(
            "SSL verification failed for %s. "
            "Retrying without certificate validation.",
            url,
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
    Download the School Census ZIP file for a given year.

    The function attempts all supported URL patterns until
    a valid file is found and successfully downloaded.

    Args:
        year:
            School Census reference year.

    Returns:
        Path:
            Local path of the downloaded ZIP file.

    Raises:
        FileExistsError:
            Raised when a ZIP file for the requested year
            already exists locally.

        FileNotFoundError:
            Raised when none of the candidate URLs contain
            a valid ZIP file.
    """

    existing_zip = find_existing_zip(year)

    if existing_zip:
        raise FileExistsError(
            f"School Census ZIP for year {year} already exists: "
            f"{existing_zip}"
        )

    target_dir = RAW_DIR / DATASET_NAME
    target_dir.mkdir(parents=True, exist_ok=True)

    LOGGER.info("Downloading School Census ZIP for year %s.", year)

    errors = []

    for zip_url in build_census_urls(year):
        zip_path = target_dir / Path(zip_url).name

        try:
            LOGGER.info("Trying download URL: %s", zip_url)

            with get_with_ssl_retry(zip_url) as response:
                response.raise_for_status()

                with zip_path.open("wb") as file:
                    for chunk in response.iter_content(
                        chunk_size=1024 * 1024
                    ):
                        if chunk:
                            file.write(chunk)

            LOGGER.info("ZIP downloaded successfully: %s", zip_path)

            return zip_path

        except requests.RequestException as error:
            errors.append(f"{zip_url} -> {error}")

            LOGGER.warning("Failed to download ZIP from %s. Error: %s", zip_url, error)

            if zip_path.exists():
                zip_path.unlink()

    raise FileNotFoundError(
        f"Could not download School Census ZIP for year {year}. "
        f"Tried {len(errors)} URLs.\n"
        + "\n".join(errors)
    )


def should_extract_file(filename: str) -> bool:
    """
    Determine whether a CSV file should be extracted.

    The decision is based on the configured list of
    selected file keywords.

    Args:
        filename:
            File name found inside the ZIP archive.

    Returns:
        bool:
            True when the file matches the configured
            extraction rules. Otherwise False.
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
    """
    Search recursively for the configured data directory.

    Args:
        root_path:
            Root directory used as the starting point
            for the recursive search.

    Returns:
        Path:
            Path of the first matching data directory.

    Raises:
        FileNotFoundError:
            Raised when the expected directory cannot
            be found.
    """

    LOGGER.info("Searching for '%s' directory under %s.", DATA_FILE_DIR, root_path)

    for path in root_path.rglob("*"):
        if path.is_dir() and path.name.lower() == DATA_FILE_DIR:
            LOGGER.info("Data directory found: %s", path)
            return path

    raise FileNotFoundError(
        f"Could not find a '{DATA_FILE_DIR}' directory under {root_path}"
    )


def extract_selected_csv_files(
    zip_path: Path,
    year: int,
) -> list[Path]:
    """
    Extract selected CSV files from a School Census ZIP.

    Only files matching the configured extraction rules
    are persisted to the landing layer.

    Extracted files are organized by:

    - Dataset
    - Table
    - Census year
    - Ingestion timestamp

    Args:
        zip_path:
            Path of the ZIP file to be processed.

        year:
            School Census reference year.

    Returns:
        list[Path]:
            List containing all extracted file paths.

    Raises:
        FileNotFoundError:
            Raised when no matching CSV files are found
            inside the ZIP archive.
    """

    LOGGER.info("Extracting selected files from ZIP: %s", zip_path)

    LANDING_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    extracted_files = []

    with ZipFile(zip_path, "r") as zip_file:
        for member in zip_file.namelist():
            path = Path(member)
            filename = path.name

            if DATA_FILE_DIR not in [
                part.lower()
                for part in path.parts
            ]:
                continue

            table_name = get_table_by_raw_file(
                filename=filename
            )

            ingestion_timestamp = int(time.time())

            target_path = (
                LANDING_DIR
                / DATASET_NAME
                / table_name
                / str(year)
                / f"{table_name}_{ingestion_timestamp}.csv"
            )

            if not should_extract_file(filename):
                continue

            target_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            LOGGER.info("Extracting file: %s -> %s", filename, target_path)

            with zip_file.open(member) as source:
                with target_path.open("wb") as target:
                    target.write(source.read())

            extracted_files.append(target_path)

    if not extracted_files:
        raise FileNotFoundError(
            "No selected CSV files were found in the ZIP."
        )

    LOGGER.info("Extraction completed. %s files extracted.", len(extracted_files))

    return extracted_files


def extract_census_data(year: int) -> list[Path]:
    """
    Execute the extraction stage of the pipeline.

    This orchestration function is responsible for:

    1. Downloading the School Census ZIP file.
    2. Extracting the selected CSV files.
    3. Persisting files into the landing layer.

    Args:
        year:
            School Census reference year.

    Returns:
        list[Path]:
            List of extracted files generated during
            the extraction process.

    Raises:
        Exception:
            Re-raises any exception generated during
            download or extraction after logging it.
    """

    try:
        LOGGER.info("Starting extraction pipeline for year %s.", year)

        zip_path = download_census_zip(year)

        extracted_files = extract_selected_csv_files(
            zip_path,
            year,
        )

        LOGGER.info("Extraction pipeline completed successfully for year %s.", year)

        return extracted_files

    except Exception:
        LOGGER.exception("Error extracting School Census data for year %s.", year)
        raise