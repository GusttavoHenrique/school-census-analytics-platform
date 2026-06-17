import argparse
import sys

from src.config import LOGGER
from src.extract import extract_census_data
from src.load import load_landing_files
from src.transform import run_transformations
from src.database import reset_pipeline_database


def main() -> None:
    """
    Execute the complete School Census Analytics pipeline.

    This function orchestrates the end-to-end execution flow:
    - Parse command-line arguments.
    - Optionally reset database schemas.
    - Download and extract School Census files.
    - Load extracted files into the staging layer.
    - Execute analytics transformations.
    - Log execution progress and final status.

    Command-line arguments:
        --year:
            School Census year to be processed.

        --reset-db:
            If provided, resets the managed database schemas
            before executing the pipeline.

    Raises:
        SystemExit:
            Returns exit code 1 when a validation error or
            unexpected runtime exception occurs.
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

        parser.add_argument(
            "--reset-db",
            action="store_true",
            help="Reset database schemas before execution",
        )

        args = parser.parse_args()

        LOGGER.info("Starting School Census pipeline for year %s.", args.year)


        if args.reset_db:
            LOGGER.warning("Resetting database schemas before execution.")
            reset_pipeline_database()

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