import re

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATASET = "microdados_censo_escolar"
DATA_FILE_PATH = "dados"
SELECTED_FILE_KEYWORDS = [
    re.sub(r"_\d{4}$", "", keyword, flags=re.IGNORECASE).upper()
    for keyword in [
        "TABELA_ESCOLA",
        "tabela_turma",
        "Tabela_Matricula",
        "Tabela_Matricula",
        "Tabela_Docente_2025",
    ]
]

DATA_DIR = PROJECT_ROOT / "data"
LANDING_DIR = DATA_DIR / "landing"
RAW_DIR = DATA_DIR / "raw"


def find_existing_zip(year: int) -> Path | None:
    """
    Verify if an especific zip file already exists.
    """

    matches = list(
        RAW_DIR.glob(f"{DATASET}_{year}*.zip")
    )

    if matches:
        print("A ZIP file already exists for the requested census year.")
        return matches[0]  
    
    return None


def build_census_urls(year: int) -> list[str]:
    """
    Build the possible url to file in data portal.
    """

    if year < 1995:
        raise ValueError(
            f"School Census data is not available for years before 1995. "
            f"Received: {year}"
        )

    base_url = (
        f"https://download.inep.gov.br/"
        f"dados_abertos/{DATASET}_{year}"
    )

    return [
        f"{base_url}.zip",
        f"{base_url}_.zip",
    ]