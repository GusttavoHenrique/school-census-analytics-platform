import sys
import argparse

from src.extract import extract_census_data


def main() -> None:
    """
    Start the script execution.
    """

    try:
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "--year",
            type=int,
            required=True,
            help="School census year"
        )

        args = parser.parse_args()
        for file in extract_census_data(year=args.year):
            print(f"- {file}")

        print("\nExtraction completed successfully.")

    except ValueError as error:
        print(f"ERROR: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()