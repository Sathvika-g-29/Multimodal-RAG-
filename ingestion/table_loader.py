from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class ExtractedTable:
    source_path: str
    page_number: int | None
    dataframe: pd.DataFrame


def extract_tables(pdf_path: str | Path) -> list[ExtractedTable]:
    """Placeholder boundary for Camelot/Tabula integration."""
    _ = Path(pdf_path)
    return []

