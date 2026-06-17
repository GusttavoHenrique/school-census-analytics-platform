from pathlib import Path

from src.config import SQL_DIR


def load_sql_template(filename: str) -> str:
    return (SQL_DIR / filename).read_text(encoding="utf-8")


def render_sql_template(filename: str, **kwargs) -> str:
    template = load_sql_template(filename)
    return template.format(**kwargs)