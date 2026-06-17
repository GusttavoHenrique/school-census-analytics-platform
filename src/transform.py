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
    """
    Create a database schema if it does not already exist.

    Args:
        engine:
            SQLAlchemy engine used to execute the statement.

        schema_name:
            Name of the schema to be created.
    """

    schema_name = to_snake_case(schema_name)

    execute_sql(
        engine=engine,
        sql=f'CREATE SCHEMA IF NOT EXISTS "{schema_name}";',
    )


def build_select_columns(columns_mapping: dict[str, str]) -> str:
    """
    Build the SELECT clause used during analytics transformations.

    Converts source columns from the staging layer into
    aliased target columns defined in the analytics mapping.

    Example:

        co_entidade -> id_escola

    Args:
        columns_mapping:
            Mapping between source and target columns.

    Returns:
        str:
            SQL SELECT fragment containing aliased columns.
    """

    return ",\n        ".join(
        f'"{to_snake_case(source_column)}" AS "{to_snake_case(target_column)}"'
        for source_column, target_column in columns_mapping.items()
    )


def build_insert_columns(columns_mapping: dict[str, str]) -> str:
    """
    Build the target column list used by INSERT statements.

    Args:
        columns_mapping:
            Mapping between source and target columns.

    Returns:
        str:
            Comma-separated list of analytics table columns.
    """

    return ", ".join(
        f'"{to_snake_case(target_column)}"'
        for target_column in columns_mapping.values()
    )


def build_table_columns(columns_mapping: dict[str, str]) -> str:
    """
    Build the analytics table column definition block.

    All generated columns are created as text fields
    to preserve compatibility with source data.

    Args:
        columns_mapping:
            Mapping between source and target columns.

    Returns:
        str:
            SQL column definition fragment.
    """

    return ",\n    ".join(
        f'"{to_snake_case(target_column)}" text'
        for target_column in columns_mapping.values()
    )


def get_surrogate_key_column(target_table: str) -> str:
    """
    Generate the surrogate key column name for an analytics table.

    Examples:

        dim_escola -> sk_escola
        dim_docente -> sk_docente
        fato_matricula -> sk_matricula

    Args:
        target_table:
            Analytics table name.

    Returns:
        str:
            Generated surrogate key column name.
    """

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
    """
    Transform data from a staging table into an analytics table.

    The transformation process performs:

    1. Analytics table creation (if necessary).
    2. Deletion of existing records for the target year.
    3. Insertion of transformed records.

    Args:
        engine:
            SQLAlchemy engine used during execution.

        source_table:
            Source staging table name.

        target_table:
            Destination analytics table name.

        year_column:
            Source column used for year filtering.

        columns_mapping:
            Mapping between source and target columns.

        year:
            School Census year being processed.
    """

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
    """
    Create and populate static dimension tables.

    These dimensions contain controlled reference values
    used by the analytics layer, such as:

    - Administrative dependency
    - School location

    Args:
        engine:
            SQLAlchemy engine used during execution.
    """

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
    """
    Execute all analytics transformations.

    This function orchestrates the analytics layer creation:

    1. Creates the analytics schema.
    2. Creates static dimensions.
    3. Processes all configured table mappings.
    4. Loads analytics tables.

    Args:
        year:
            School Census year being processed.
    """

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