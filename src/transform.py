from src.config import (
    LOGGER,
    DATABASE_STAGING_SCHEMA,
    DATABASE_ANALYTICS_SCHEMA,
    ANALYTICS_TABLE_MAPPINGS,
)
from src.database import get_engine, execute_sql
from src.utils import to_snake_case


def create_schema(engine, schema_name: str) -> None:
    schema_name = to_snake_case(schema_name)

    execute_sql(
        engine=engine,
        sql=f'CREATE SCHEMA IF NOT EXISTS "{schema_name}";',
    )


def build_select_columns(columns_mapping: dict[str, str]) -> str:
    return ",\n        ".join(
        f'"{to_snake_case(source_column)}" AS "{to_snake_case(target_column)}"'
        for source_column, target_column in columns_mapping.items()
    )


def build_insert_columns(columns_mapping: dict[str, str]) -> str:
    return ", ".join(
        f'"{to_snake_case(target_column)}"'
        for target_column in columns_mapping.values()
    )


def transform_table(
    engine,
    source_table: str,
    target_table: str,
    columns_mapping: dict[str, str],
    year: int,
) -> None:
    source_schema = to_snake_case(DATABASE_STAGING_SCHEMA)
    target_schema = to_snake_case(DATABASE_ANALYTICS_SCHEMA)
    source_table = to_snake_case(source_table)
    target_table = to_snake_case(target_table)

    select_columns = build_select_columns(columns_mapping)
    insert_columns = build_insert_columns(columns_mapping)

    LOGGER.info(
        "Transforming %s.%s into %s.%s for year %s.",
        source_schema,
        source_table,
        target_schema,
        target_table,
        year,
    )

    sql = f"""
        CREATE TABLE IF NOT EXISTS "{target_schema}"."{target_table}" AS
        SELECT
            {select_columns}
        FROM "{source_schema}"."{source_table}"
        WHERE 1 = 0;

        DELETE FROM "{target_schema}"."{target_table}"
        WHERE census_year = :year;

        INSERT INTO "{target_schema}"."{target_table}" (
            {insert_columns}
        )
        SELECT
            {select_columns}
        FROM "{source_schema}"."{source_table}"
        WHERE nu_ano_censo = :year;
    """

    execute_sql(
        engine=engine,
        sql=sql,
        params={"year": str(year)},
    )


def run_transformations(year: int) -> None:
    engine = get_engine()

    create_schema(engine, DATABASE_ANALYTICS_SCHEMA)

    for source_table, config in ANALYTICS_TABLE_MAPPINGS.items():
        transform_table(
            engine=engine,
            source_table=source_table,
            target_table=config["target_table"],
            columns_mapping=config["columns"],
            year=year,
        )

    LOGGER.info("Analytics transformations completed successfully for year %s.", year)