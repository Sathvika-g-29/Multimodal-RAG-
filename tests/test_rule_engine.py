from reasoning.rule_engine import answer_with_rules
from ingestion.enhanced_dataset_parser import (
    _conflict_documents,
    _eligibility_documents,
    _hiring_documents,
    _statistics_documents,
    _trend_documents,
)


def sample_corpus(tmp_path):
    path = tmp_path / "Placement_RAG_Dataset_Enhanced.pdf"
    return (
        _eligibility_documents(path)
        + _hiring_documents(path)
        + _trend_documents(path)
        + _conflict_documents(path)
        + _statistics_documents(path)
    )


def test_rule_engine_answers_conflicting_amazon_cgpa(tmp_path) -> None:
    answer = answer_with_rules("Is the Amazon CGPA cutoff 6.4 or 7.0?", sample_corpus(tmp_path))

    assert answer is not None
    assert "conflicting records" in answer.text
    assert "6.4" in answer.text
    assert "7.0" in answer.text


def test_rule_engine_answers_most_interns(tmp_path) -> None:
    answer = answer_with_rules("Which company hires the most Interns?", sample_corpus(tmp_path))

    assert answer is not None
    assert "Oracle" in answer.text
    assert "95" in answer.text


def test_rule_engine_answers_largest_package_growth(tmp_path) -> None:
    answer = answer_with_rules(
        "Which company's package grew the most from 2021 to 2024?",
        sample_corpus(tmp_path),
    )

    assert answer is not None
    assert "Infosys" in answer.text
    assert "6.9" in answer.text


def test_rule_engine_handles_low_cgpa_edge_case(tmp_path) -> None:
    answer = answer_with_rules("I have CGPA 5.0. Where can I apply?", sample_corpus(tmp_path))

    assert answer is not None
    assert "No company" in answer.text


def test_rule_engine_answers_python_company_with_most_interns(tmp_path) -> None:
    answer = answer_with_rules("Which Python-focused company hires the most Interns?", sample_corpus(tmp_path))

    assert answer is not None
    assert "Oracle" in answer.text
    assert "95" in answer.text


def test_rule_engine_answers_package_to_cgpa_ratio(tmp_path) -> None:
    answer = answer_with_rules("Which company offers the best package-to-CGPA ratio?", sample_corpus(tmp_path))

    assert answer is not None
    assert "Intel" in answer.text


def test_rule_engine_answers_generic_conflict_query(tmp_path) -> None:
    answer = answer_with_rules("Which company had conflicting CGPA data across sources?", sample_corpus(tmp_path))

    assert answer is not None
    assert "Amazon" in answer.text
    assert "Microsoft" in answer.text
