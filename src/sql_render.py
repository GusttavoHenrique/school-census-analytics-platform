from pathlib import Path

from src.config import SQL_DIR


def load_sql_template(filename: str) -> str:
    """
    Load a SQL template file from the project's SQL directory.

    Args:
        filename:
            Name of the SQL file to be loaded.

    Returns:
        str:
            SQL template content as a string.

    Raises:
        FileNotFoundError:
            Raised when the requested SQL file does not exist.
    """

    return (SQL_DIR / filename).read_text(encoding="utf-8")


def render_sql_template(filename: str, **kwargs) -> str:
    """
    Render a SQL template using keyword arguments.

    The function loads a SQL template file and replaces
    placeholders using Python string formatting.

    Example:
        Template:

            SELECT * FROM {schema}.{table};

        Call:

            render_sql_template(
                "query.sql",
                schema="analytics",
                table="dim_escola",
            )

    Args:
        filename:
            Name of the SQL template file.

        **kwargs:
            Values used to replace template placeholders.

    Returns:
        str:
            Rendered SQL statement ready for execution.

    Raises:
        KeyError:
            Raised when a required template variable is
            not provided.
    """

    template = load_sql_template(filename)
    return template.format(**kwargs)