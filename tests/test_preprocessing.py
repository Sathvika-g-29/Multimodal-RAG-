from preprocessing.chunker import chunk_text
from preprocessing.cleaner import normalize_text
from preprocessing.deduplicator import deduplicate_texts


def test_normalize_text_collapses_whitespace() -> None:
    assert normalize_text("Amazon\n\n  SDE\t7.5") == "Amazon SDE 7.5"


def test_deduplicate_texts_is_case_insensitive() -> None:
    assert deduplicate_texts(["Google", " google ", "Microsoft"]) == ["Google", "Microsoft"]


def test_chunk_text_preserves_metadata() -> None:
    chunks = chunk_text("abcdef", {"company": "TCS"}, chunk_size=4, overlap=1)
    assert chunks[0].metadata["company"] == "TCS"
    assert [chunk.text for chunk in chunks] == ["abcd", "def"]

