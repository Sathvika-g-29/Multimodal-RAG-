from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class ExtractedTable:
    source_path: str
    page_number: int | None
    dataframe: pd.DataFrame


def extract_tables(pdf_path: str | Path) -> list[ExtractedTable]:
    path = Path(pdf_path)

    try:
        import camelot
    except ImportError:
        return []

    tables = camelot.read_pdf(str(path), pages="all", flavor="stream")
    extracted: list[ExtractedTable] = []
    for table in tables:
        page_number = int(table.page) if str(table.page).isdigit() else None
        extracted.append(
            ExtractedTable(
                source_path=str(path),
                page_number=page_number,
                dataframe=table.df,
            )
        )

    return extracted


def dataframe_to_records(dataframe: pd.DataFrame) -> list[str]:
    if dataframe.empty:
        return []

    frame = dataframe.copy()
    frame = frame.replace("", pd.NA).dropna(how="all")
    return [
        "; ".join(f"col_{index + 1}: {value}" for index, value in enumerate(row) if pd.notna(value))
        for row in frame.itertuples(index=False, name=None)
    ]
