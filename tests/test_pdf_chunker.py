from preprocessing.pdf_chunker import chunk_pdf_text_by_structure


def test_chunk_pdf_text_by_structure_returns_text() -> None:
    chunks = chunk_pdf_text_by_structure("Section 1: Eligibility\nAmazon CGPA 6.4")

    assert chunks
    assert "Amazon" in chunks[0]
