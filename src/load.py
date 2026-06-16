from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

from src.config import DATABASE_URL, LANDING_DIR, DATASET_NAME, LOGGER
from src.utils import get_table_by_landing_file, to_snake_case


STAGING_SCHEMA = "staging"


def get_engine():
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL is not configured.")

    LOGGER.info("Creating database engine.")
    return create_engine(DATABASE_URL)


def create_schema(engine, schema_name: str) -> None:
    schema_name = to_snake_case(schema_name)

    LOGGER.info("Creating schema if not exists: %s", schema_name)

    with engine.begin() as conn:
        conn.execute(
            text(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}";')
        )


def create_staging_table_if_not_exists(
    engine,
    file_path: Path,
    schema_name: str,
    table_name: str,
) -> None:
    LOGGER.info(
        "Creating table if not exists: %s.%s",
        schema_name,
        table_name,
    )

    sample = pd.read_csv(
        file_path,
        sep=";",
        encoding="latin1",
        nrows=100,
        low_memory=False,
    )

    columns = [to_snake_case(column) for column in sample.columns]

    columns_sql = ", ".join(
        f'"{column}" text'
        for column in columns
    )

    with engine.begin() as conn:
        conn.execute(
            text(
                f"""
                CREATE TABLE IF NOT EXISTS "{schema_name}"."{table_name}" (
                    {columns_sql}
                );
                """
            )
        )


def delete_existing_year(
    engine,
    schema_name: str,
    table_name: str,
    year: int,
) -> None:
    LOGGER.info(
        "Deleting existing rows from %s.%s for census year %s.",
        schema_name,
        table_name,
        year,
    )

    with engine.begin() as conn:
        conn.execute(
            text(
                f"""
                DELETE FROM "{schema_name}"."{table_name}"
                WHERE nu_ano_censo = :year;
                """
            ),
            {"year": str(year)},
        )


def copy_csv_to_postgres(
    engine,
    file_path: Path,
    schema_name: str,
    table_name: str,
) -> None:
    LOGGER.info(
        "Copying CSV file into PostgreSQL table: %s -> %s.%s",
        file_path,
        schema_name,
        table_name,
    )

    connection = engine.raw_connection()

    try:
        with connection.cursor() as cursor:
            with open(file_path, "r", encoding="latin1") as file:
                header = file.readline().strip()

                columns = [
                    to_snake_case(column)
                    for column in header.split(";")
                ]

                quoted_columns = ", ".join(
                    f'"{column}"'
                    for column in columns
                )

                copy_sql = f"""
                    COPY "{schema_name}"."{table_name}" ({quoted_columns})
                    FROM STDIN
                    WITH (
                        FORMAT CSV,
                        HEADER FALSE,
                        DELIMITER ';',
                        ENCODING 'LATIN1'
                    );
                """

                cursor.copy_expert(copy_sql, file)

        connection.commit()

        LOGGER.info(
            "CSV copy completed successfully for table: %s.%s",
            schema_name,
            table_name,
        )

    except Exception:
        connection.rollback()

        LOGGER.exception(
            "Failed to copy CSV file into table: %s.%s",
            schema_name,
            table_name,
        )

        raise

    finally:
        connection.close()


def load_csv_to_postgres(
    engine,
    file_path: Path,
    schema_name: str,
    table_name: str,
    year: int,
) -> None:
    schema_name = to_snake_case(schema_name)
    table_name = to_snake_case(table_name)

    LOGGER.info(
        "Starting load for file %s into %s.%s.",
        file_path,
        schema_name,
        table_name,
    )

    create_staging_table_if_not_exists(
        engine=engine,
        file_path=file_path,
        schema_name=schema_name,
        table_name=table_name,
    )

    delete_existing_year(
        engine=engine,
        schema_name=schema_name,
        table_name=table_name,
        year=year,
    )

    copy_csv_to_postgres(
        engine=engine,
        file_path=file_path,
        schema_name=schema_name,
        table_name=table_name,
    )

    LOGGER.info(
        "Finished loading table: %s.%s",
        schema_name,
        table_name,
    )


def get_landing_file_timestamp(file_path: Path) -> int:
    _, timestamp = get_table_by_landing_file(file_path)
    return timestamp


def load_landing_files(year: int) -> None:
    landing_root = LANDING_DIR / DATASET_NAME

    LOGGER.info(
        "Starting landing load for year %s from path: %s",
        year,
        landing_root,
    )

    if not landing_root.exists():
        raise FileNotFoundError(
            f"Landing path not found: {landing_root}"
        )

    engine = get_engine()
    create_schema(engine, STAGING_SCHEMA)

    loaded_files = 0

    for table_dir in landing_root.iterdir():
        if not table_dir.is_dir():
            continue

        year_dir = table_dir / str(year)

        if not year_dir.exists():
            LOGGER.debug(
                "Skipping table directory without year folder: %s",
                year_dir,
            )
            continue

        csv_files = list(year_dir.glob("*.csv"))

        if not csv_files:
            LOGGER.debug(
                "No CSV files found in year directory: %s",
                year_dir,
            )
            continue

        latest_file = max(
            csv_files,
            key=get_landing_file_timestamp,
        )

        table_name, timestamp = get_table_by_landing_file(latest_file)
        table_name = to_snake_case(table_name)

        LOGGER.info(
            "Selected latest file for table %s: %s (timestamp=%s)",
            table_name,
            latest_file.name,
            timestamp,
        )

        load_csv_to_postgres(
            engine=engine,
            file_path=latest_file,
            schema_name=STAGING_SCHEMA,
            table_name=table_name,
            year=year,
        )

        loaded_files += 1

    if loaded_files == 0:
        raise FileNotFoundError(
            f"No CSV files found for year {year} under {landing_root}"
        )

    LOGGER.info(
        "Landing load completed successfully. Loaded files: %s",
        loaded_files,
    )