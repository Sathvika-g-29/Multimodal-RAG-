from vectordb.chroma_store import _metadata_for_chroma, _where_filter


def test_metadata_for_chroma_removes_none_and_complex_values() -> None:
    metadata = _metadata_for_chroma(
        {
            "company": "Amazon",
            "year": 2024,
            "missing": None,
            "bad": {"nested": True},
        }
    )

    assert metadata == {"company": "Amazon", "year": 2024}


def test_where_filter_ignores_empty_values() -> None:
    assert _where_filter({"company": "Google", "year": None}) == {"company": "Google"}
    assert _where_filter({"company": None}) is None


def test_where_filter_uses_and_for_multiple_values() -> None:
    assert _where_filter({"company": "Google", "section": "eligibility"}) == {
        "$and": [{"company": "Google"}, {"section": "eligibility"}]
    }
