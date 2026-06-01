from ingestion.batch_ingestion import iter_supported_files
from ingestion.batch_ingestion import _deduplicate_documents
from ingestion.document import SourceDocument
from ingestion.file_registry import register_file


def test_iter_supported_files_discovers_known_types(tmp_path) -> None:
    pdf = tmp_path / "a.pdf"
    txt = tmp_path / "ignore.txt"
    pdf.write_text("x", encoding="utf-8")
    txt.write_text("x", encoding="utf-8")

    assert iter_supported_files([tmp_path]) == [pdf]


def test_register_file_detects_duplicates(tmp_path) -> None:
    file_path = tmp_path / "a.pdf"
    file_path.write_text("same", encoding="utf-8")
    registry = {}

    _, first_seen = register_file(file_path, registry)
    _, second_seen = register_file(file_path, registry)

    assert first_seen is False
    assert second_seen is True


def test_deduplicate_documents_keeps_one_copy() -> None:
    first = SourceDocument.create("same text", "a.pdf", "pdf_text")
    second = SourceDocument.create("same text", "b.pdf", "pdf_text")

    assert _deduplicate_documents([first, second]) == [first]
