import json
from collections.abc import Iterable
from pathlib import Path

from ingestion.document import SourceDocument
from preprocessing.cleaner import normalize_text
from preprocessing.pdf_chunker import chunk_pdf_text_by_structure


PDF_EXTENSIONS = {".pdf"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"}
TABLE_EXTENSIONS = {".csv", ".xlsx", ".xls"}


def infer_metadata(path: Path) -> dict[str, str | int | float | bool | None]:
    tokens = path.stem.replace("-", "_").split("_")
    metadata: dict[str, str | int | float | bool | None] = {
        "source_file": path.name,
    }

    for token in tokens:
        if token.isdigit() and len(token) == 4:
            metadata["year"] = int(token)

    if tokens:
        metadata["collection_hint"] = tokens[0].casefold()

    return metadata


def documents_from_pdf(pdf_path: str | Path) -> list[SourceDocument]:
    from ingestion.table_loader import dataframe_to_records, extract_tables
    from ingestion.text_loader import extract_pdf_text

    path = Path(pdf_path)
    documents: list[SourceDocument] = []

    for page in extract_pdf_text(path):
        page_text = normalize_text(page.text)
        for text in chunk_pdf_text_by_structure(page_text):
            metadata = infer_metadata(path) | {"page": page.page_number, "modality": "text"}
            documents.append(SourceDocument.create(text, str(path), "pdf_text", metadata))

    for table in extract_tables(path):
        for row_text in dataframe_to_records(table.dataframe):
            text = normalize_text(row_text)
            if text:
                metadata = infer_metadata(path) | {
                    "page": table.page_number,
                    "modality": "table",
                }
                documents.append(SourceDocument.create(text, str(path), "pdf_table", metadata))

    return documents


def documents_from_image(image_path: str | Path) -> list[SourceDocument]:
    from ingestion.ocr_pipeline import extract_image_text

    path = Path(image_path)
    text = normalize_text(extract_image_text(path))
    if not text:
        return []

    metadata = infer_metadata(path) | {"modality": "image_ocr"}
    return [SourceDocument.create(text, str(path), "image_ocr", metadata)]


def documents_from_table(table_path: str | Path) -> list[SourceDocument]:
    import pandas as pd

    path = Path(table_path)
    if path.suffix.casefold() == ".csv":
        frame = pd.read_csv(path)
    else:
        frame = pd.read_excel(path)

    documents: list[SourceDocument] = []
    for row_number, row in enumerate(frame.to_dict(orient="records"), start=1):
        text = "; ".join(f"{key}: {value}" for key, value in row.items() if not pd.isna(value))
        text = normalize_text(text)
        if text:
            metadata = infer_metadata(path) | {"row": row_number, "modality": "structured_table"}
            documents.append(SourceDocument.create(text, str(path), "structured_table", metadata))

    return documents


def discover_files(directory: str | Path, extensions: set[str]) -> list[Path]:
    path = Path(directory)
    if not path.exists():
        return []
    return sorted(
        file_path
        for file_path in path.rglob("*")
        if file_path.is_file() and file_path.suffix.casefold() in extensions
    )


def build_corpus(
    pdf_dir: str | Path = "data/pdfs",
    image_dir: str | Path = "data/images",
    table_dir: str | Path = "data/tables",
) -> list[SourceDocument]:
    documents: list[SourceDocument] = []

    for pdf_path in discover_files(pdf_dir, PDF_EXTENSIONS):
        documents.extend(documents_from_pdf(pdf_path))

    for image_path in discover_files(image_dir, IMAGE_EXTENSIONS):
        documents.extend(documents_from_image(image_path))

    for table_path in discover_files(table_dir, TABLE_EXTENSIONS):
        documents.extend(documents_from_table(table_path))

    return documents


def write_jsonl(documents: Iterable[SourceDocument], output_path: str | Path) -> int:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    count = 0
    with path.open("w", encoding="utf-8") as file:
        for document in documents:
            file.write(json.dumps(document.to_dict(), ensure_ascii=False) + "\n")
            count += 1

    return count


def append_jsonl(documents: Iterable[SourceDocument], output_path: str | Path) -> int:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    count = 0
    with path.open("a", encoding="utf-8") as file:
        for document in documents:
            file.write(json.dumps(document.to_dict(), ensure_ascii=False) + "\n")
            count += 1

    return count
