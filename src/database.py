from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from src.config import DATABASE_URL, LOGGER


def get_engine() -> Engine:
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL is not configured.")

    LOGGER.info("Creating database engine.")
    return create_engine(DATABASE_URL)


def execute_sql(
    engine: Engine,
    sql: str,
    params: dict | None = None,
) -> None:
    with engine.begin() as conn:
        conn.execute(text(sql), params or {})


def reset_pipeline_database() -> None:
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