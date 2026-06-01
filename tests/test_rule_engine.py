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


def test_rule_engine_answers_direct_bond_without_conflict_noise(tmp_path) -> None:
    answer = answer_with_rules("What is the bond period for Amazon?", sample_corpus(tmp_path))

    assert answer is not None
    assert "2 year" in answer.text
    assert "conflicting" not in answer.text.casefold()


def test_rule_engine_answers_direct_backlog_query(tmp_path) -> None:
    answer = answer_with_rules("Does Microsoft allow backlogs?", sample_corpus(tmp_path))

    assert answer is not None
    assert "1 backlog" in answer.text


def test_rule_engine_compares_all_dimensions(tmp_path) -> None:
    answer = answer_with_rules(
        "Compare Google and Amazon on all dimensions: eligibility, package, hiring, trend.",
        sample_corpus(tmp_path),
    )

    assert answer is not None
    assert "Google" in answer.text
    assert "Amazon" in answer.text
    assert "growth" in answer.text


def test_rule_engine_routes_ceo_question_to_web_tool(tmp_path, monkeypatch) -> None:
    def fake_lookup(query):
        from tools.web_lookup_tool import WebLookupResult

        return WebLookupResult(
            query=query,
            answer="K. Krithivasan is the CEO of TCS.",
            source_url="https://example.com/tcs",
            status="ok",
        )

    monkeypatch.setattr("tools.web_lookup_tool.web_lookup", fake_lookup)

    answer = answer_with_rules("Who is the CEO of TCS?", sample_corpus(tmp_path))

    assert answer is not None
    assert "web lookup tool" in answer.text
    assert "K. Krithivasan" in answer.text


def test_rule_engine_asks_for_student_id_when_eligibility_profile_missing(tmp_path) -> None:
    answer = answer_with_rules("Am I eligible for TCS?", sample_corpus(tmp_path))

    assert answer is not None
    assert "student ID" in answer.text


def test_rule_engine_uses_student_profile_tool_for_eligibility(tmp_path) -> None:
    answer = answer_with_rules(
        "Am I eligible for TCS? my roll number is 22B01A0001",
        sample_corpus(tmp_path),
    )

    assert answer is not None
    assert "not eligible for TCS" in answer.text
