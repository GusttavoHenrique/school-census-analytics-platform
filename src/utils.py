import re
from pathlib import Path


def get_table_by_raw_file(filename: str) -> str:
    return re.sub(
        r"^tabela_|_\d{4}\.csv$",
        "",
        filename,
        flags=re.IGNORECASE,
    ).lower()


def get_table_by_landing_file(file_path: Path) -> tuple[str, int]:
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
    value = value.strip().lower()
    value = re.sub(r"[^\w]+", "_", value)
    value = re.sub(r"_+", "_", value)

    return value.strip("_")