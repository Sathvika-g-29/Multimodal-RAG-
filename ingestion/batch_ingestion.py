from collections.abc import Iterable
from pathlib import Path

from ingestion.document import SourceDocument
from ingestion.file_registry import DEFAULT_REGISTRY_PATH, load_registry, register_file, save_registry
from ingestion.pipeline import (
    IMAGE_EXTENSIONS,
    PDF_EXTENSIONS,
    TABLE_EXTENSIONS,
    documents_from_image,
    documents_from_pdf,
    documents_from_table,
)
from preprocessing.deduplicator import deduplicate_texts


def iter_supported_files(paths: Iterable[str | Path]) -> list[Path]:
    files: list[Path] = []
    for item in paths:
        path = Path(item)
        if path.is_file() and _is_supported(path):
            files.append(path)
        elif path.is_dir():
            files.extend(
                file
                for file in path.rglob("*")
                if file.is_file() and _is_supported(file)
            )
    return sorted(files)


def ingest_files_incrementally(
    paths: Iterable[str | Path],
    registry_path: str | Path = DEFAULT_REGISTRY_PATH,
) -> tuple[list[SourceDocument], list[Path]]:
    registry = load_registry(registry_path)
    documents: list[SourceDocument] = []
    skipped: list[Path] = []

    for file_path in iter_supported_files(paths):
        _, already_seen = register_file(file_path, registry)
        if already_seen:
            skipped.append(file_path)
            continue
        documents.extend(_documents_from_supported_file(file_path))

    documents = _deduplicate_documents(documents)
    save_registry(registry, registry_path)
    return documents, skipped


def _documents_from_supported_file(path: Path) -> list[SourceDocument]:
    suffix = path.suffix.casefold()
    if suffix in PDF_EXTENSIONS:
        return documents_from_pdf(path)
    if suffix in IMAGE_EXTENSIONS:
        return documents_from_image(path)
    if suffix in TABLE_EXTENSIONS:
        return documents_from_table(path)
    return []


def _deduplicate_documents(documents: list[SourceDocument]) -> list[SourceDocument]:
    unique_texts = set(deduplicate_texts(document.text for document in documents))
    seen: set[str] = set()
    unique_documents: list[SourceDocument] = []
    for document in documents:
        if document.text not in unique_texts or document.text in seen:
            continue
        seen.add(document.text)
        unique_documents.append(document)
    return unique_documents


def _is_supported(path: Path) -> bool:
    return path.suffix.casefold() in PDF_EXTENSIONS | IMAGE_EXTENSIONS | TABLE_EXTENSIONS
