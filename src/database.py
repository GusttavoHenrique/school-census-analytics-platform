from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from src.config import DATABASE_URL, LOGGER, SQL_DIR


def get_engine() -> Engine:
    """
    Create and return a SQLAlchemy engine instance.

    Returns:
        Engine:
            Configured SQLAlchemy engine connected to the
            PostgreSQL database defined by DATABASE_URL.

    Raises:
        ValueError:
            Raised when DATABASE_URL is not configured.
    """

    if not DATABASE_URL:
        raise ValueError("DATABASE_URL is not configured.")

    LOGGER.info("Creating database engine.")
    return create_engine(DATABASE_URL)


def execute_sql(
    engine: Engine,
    sql: str,
    params: dict | None = None,
) -> None:
    """
    Execute a SQL statement within a transactional context.

    Args:
        engine:
            SQLAlchemy engine used to establish the connection.

        sql:
            SQL statement to be executed.

        params:
            Optional dictionary containing SQL parameters.
    """

    with engine.begin() as conn:
        conn.execute(text(sql), params or {})


def create_metrics_views() -> None:
    """
    Create analytical metric views.

    Executes the SQL script responsible for creating all
    reporting views required by the challenge.

    The SQL file is expected to be available under the
    project's SQL directory as:

    - 04_create_metrics_views.sql
    """

    LOGGER.info("Creating analytical metric views.")

    engine = get_engine()

    sql = (
        SQL_DIR
        / "04_create_metrics_views.sql"
    ).read_text(encoding="utf-8")

    execute_sql(
        engine=engine,
        sql=sql,
    )

    LOGGER.info("Analytical metric views created successfully.")


def reset_pipeline_database() -> None:
    """
    Remove all schemas managed by the pipeline.

    This operation is primarily intended for development,
    testing and recovery scenarios where the database
    storage limit has been exceeded.

    The following schemas are removed:

    - staging
    - analytics

    All dependent objects are dropped using CASCADE.
    """

    LOGGER.warning("Resetting pipeline database schemas due to storage limit")
    
    engine = get_engine()

    execute_sql(
        engine=engine,
        sql="""
        DROP SCHEMA IF EXISTS staging CASCADE;
        DROP SCHEMA IF EXISTS analytics CASCADE;
        """,
    )

    LOGGER.info("Database reset completed successfully.")