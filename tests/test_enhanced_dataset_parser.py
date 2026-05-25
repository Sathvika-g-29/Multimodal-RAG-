from ingestion.enhanced_dataset_parser import (
    _conflict_documents,
    _eligibility_documents,
    _hiring_documents,
    _trend_documents,
)


def test_eligibility_documents_are_company_rows(tmp_path) -> None:
    documents = _eligibility_documents(tmp_path / "Placement_RAG_Dataset_Enhanced.pdf")

    amazon = next(document for document in documents if document.metadata["company"] == "Amazon")

    assert len(documents) == 20
    assert amazon.metadata["min_cgpa"] == 6.4
    assert amazon.metadata["max_backlogs"] == 1
    assert amazon.metadata["section"] == "eligibility"


def test_hiring_documents_keep_role_counts(tmp_path) -> None:
    documents = _hiring_documents(tmp_path / "Placement_RAG_Dataset_Enhanced.pdf")

    oracle = next(document for document in documents if document.metadata["company"] == "Oracle")

    assert oracle.metadata["intern_roles"] == 95
    assert oracle.metadata["total_roles"] == 284


def test_trend_documents_compute_absolute_growth(tmp_path) -> None:
    documents = _trend_documents(tmp_path / "Placement_RAG_Dataset_Enhanced.pdf")

    infosys = next(document for document in documents if document.metadata["company"] == "Infosys")

    assert infosys.metadata["increase_2021_2024"] == 6.9


def test_conflict_documents_keep_official_and_portal_records(tmp_path) -> None:
    documents = _conflict_documents(tmp_path / "Placement_RAG_Dataset_Enhanced.pdf")
    amazon_documents = [document for document in documents if document.metadata["company"] == "Amazon"]

    assert len(amazon_documents) == 2
    assert {document.metadata["source_authority"] for document in amazon_documents} == {
        "official",
        "portal",
    }
