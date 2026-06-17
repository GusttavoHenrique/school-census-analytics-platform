import re
from pathlib import Path


def get_table_by_raw_file(filename: str) -> str:
    """
    Extract the table name from a raw School Census CSV file.

    The function removes common prefixes and suffixes
    used by INEP file naming conventions.

    Example:
        tabela_escola_2025.csv -> escola

    Args:
        filename:
            Raw CSV filename.

    Returns:
        str:
            Normalized table name in lowercase.
    """

    return re.sub(
        r"^tabela_|_\d{4}\.csv$",
        "",
        filename,
        flags=re.IGNORECASE,
    ).lower()


def get_table_by_landing_file(file_path: Path) -> tuple[str, int]:
    """
    Extract table metadata from a landing file name.

    Landing files follow the convention:

        <table_name>_<timestamp>.csv

    Example:

        escola_1718843201.csv

    Returns:

        ("escola", 1718843201)

    Args:
        file_path:
            Path of the landing file.

    Returns:
        tuple[str, int]:
            Tuple containing:

            - Table name
            - Ingestion timestamp

    Raises:
        ValueError:
            Raised when the file name does not follow
            the expected landing file convention.
    """

    match = re.match(
        r"^(.*?)_(\d+)\.csv$",
        file_path.name,
        flags=re.IGNORECASE,
    )

    if not match:
        raise ValueError(
            f"Could not extract metadata from file: {file_path}"
        )

    return (
        match.group(1).lower(),
        int(match.group(2)),
    )


def to_snake_case(value: str) -> str:
    """
    Convert a string into snake_case format.

    The function:

    - Converts text to lowercase;
    - Replaces non-alphanumeric characters with "_";
    - Collapses consecutive underscores;
    - Removes leading and trailing underscores.

    Example:

        "Nome da Escola" -> "nome_da_escola"

    Args:
        value:
            Input string to be normalized.

    Returns:
        str:
            Normalized snake_case string.
    """

    value = value.strip().lower()
    value = re.sub(r"[^\w]+", "_", value)
    value = re.sub(r"_+", "_", value)

    return value.strip("_")