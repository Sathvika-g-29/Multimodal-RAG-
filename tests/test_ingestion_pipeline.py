import json

from ingestion.document import SourceDocument
from ingestion.pipeline import infer_metadata, write_jsonl


def test_infer_metadata_extracts_year_from_filename(tmp_path) -> None:
    path = tmp_path / "amazon_2024_sde.pdf"

    metadata = infer_metadata(path)

    assert metadata["year"] == 2024
    assert metadata["collection_hint"] == "amazon"


def test_write_jsonl_persists_source_documents(tmp_path) -> None:
    output_path = tmp_path / "corpus.jsonl"
    document = SourceDocument.create(
        text="Google SDE cutoff 7.5 CGPA",
        source_path="data/pdfs/google_2024.pdf",
        source_type="pdf_text",
        metadata={"company": "Google"},
    )

    count = write_jsonl([document], output_path)
    saved = json.loads(output_path.read_text(encoding="utf-8"))

    assert count == 1
    assert saved["text"] == "Google SDE cutoff 7.5 CGPA"
    assert saved["metadata"]["company"] == "Google"
