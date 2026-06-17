from src.config import (
    LOGGER,
    DATABASE_STAGING_SCHEMA,
    DATABASE_ANALYTICS_SCHEMA,
    ANALYTICS_TABLE_MAPPINGS,
)
from src.database import get_engine, execute_sql
from src.sql_render import render_sql_template
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


def build_table_columns(columns_mapping: dict[str, str]) -> str:
    return ",\n    ".join(
        f'"{to_snake_case(target_column)}" text'
        for target_column in columns_mapping.values()
    )


def get_surrogate_key_column(target_table: str) -> str:
    target_table = to_snake_case(target_table)

    if target_table.startswith("dim_"):
        return f"sk_{target_table.replace('dim_', '')}"

    if target_table.startswith("fato_"):
        return f"sk_{target_table.replace('fato_', '')}"

    return f"sk_{target_table}"


def transform_table(
    engine,
    source_table: str,
    target_table: str,
    year_column: str,
    columns_mapping: dict[str, str],
    year: int,
) -> None:
    source_schema = to_snake_case(DATABASE_STAGING_SCHEMA)
    target_schema = to_snake_case(DATABASE_ANALYTICS_SCHEMA)
    source_table = to_snake_case(source_table)
    target_table = to_snake_case(target_table)

    source_year_column = to_snake_case(year_column)
    target_year_column = to_snake_case(columns_mapping[year_column])

    surrogate_key_column = get_surrogate_key_column(target_table)
    table_columns = build_table_columns(columns_mapping)
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

    create_table_sql = render_sql_template(
        "02_create_analytics_table.sql",
        target_schema=target_schema,
        target_table=target_table,
        surrogate_key_column=surrogate_key_column,
        table_columns=table_columns,
    )

    execute_sql(engine=engine, sql=create_table_sql)

    load_table_sql = render_sql_template(
        "03_load_analytics_table.sql",
        source_schema=source_schema,
        source_table=source_table,
        target_schema=target_schema,
        target_table=target_table,
        source_year_column=source_year_column,
        target_year_column=target_year_column,
        insert_columns=insert_columns,
        select_columns=select_columns,
    )

    execute_sql(
        engine=engine,
        sql=load_table_sql,
        params={"year": str(year)},
    )


def create_static_dimension_tables(engine) -> None:
    target_schema = to_snake_case(DATABASE_ANALYTICS_SCHEMA)

    LOGGER.info(
        "Creating static dimension tables in schema %s.",
        target_schema,
    )

    sql = render_sql_template(
        "01_create_static_dimensions.sql",
        target_schema=target_schema,
    )

    execute_sql(engine=engine, sql=sql)


def run_transformations(year: int) -> None:
    engine = get_engine()

    create_schema(
        engine=engine,
        schema_name=DATABASE_ANALYTICS_SCHEMA,
    )

    create_static_dimension_tables(engine)

    for source_table, config in ANALYTICS_TABLE_MAPPINGS.items():
        transform_table(
            engine=engine,
            source_table=source_table,
            target_table=config["target_table"],
            year_column=config["year"],
            columns_mapping=config["columns"],
            year=year,
        )

    LOGGER.info(
        "Analytics transformations completed successfully for year %s.",
        year,
    )