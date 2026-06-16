import argparse
import sys

from src.config import LOGGER
from src.extract import extract_census_data
from src.load import load_landing_files
from src.transform import run_transformations


def main() -> None:
    """
    Start the pipeline execution.
    """

    try:
        parser = argparse.ArgumentParser(
            description="School Census Analytics Platform"
        )

        parser.add_argument(
            "--year",
            type=int,
            required=True,
            help="School census year",
        )

        args = parser.parse_args()

        LOGGER.info("Starting School Census pipeline for year %s.", args.year)

        extracted_files = extract_census_data(
            year=args.year,
        )

        LOGGER.info("Extraction completed successfully. Extracted files: %s", len(extracted_files))

        for file_path in extracted_files:
            LOGGER.info("Extracted file: %s", file_path)

        load_landing_files(
            year=args.year,
        )

        LOGGER.info("Load completed successfully for year %s.", args.year)

        run_transformations(
            year=args.year,
        )

        LOGGER.info("Transformations completed successfully for year %s.", args.year)

        LOGGER.info("Pipeline finished successfully.")

    except ValueError as error:
        LOGGER.error("Validation error: %s", error)
        sys.exit(1)

    except Exception:
        LOGGER.exception("Unexpected error during pipeline execution.")
        sys.exit(1)


if __name__ == "__main__":
    main()