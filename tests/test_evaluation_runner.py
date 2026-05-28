import json

from evaluation.runner import EvaluationResult, classify_answer, summarize_results, write_evaluation_report


def test_classify_answer_detects_conflicts() -> None:
    assert classify_answer("There are conflicting records for Amazon.") == "conflict-aware"


def test_classify_answer_detects_fallback() -> None:
    assert (
        classify_answer("I do not have enough information in the provided placement dataset.")
        == "fallback"
    )


def test_write_evaluation_report(tmp_path) -> None:
    output = tmp_path / "report.json"
    result = EvaluationResult(
        id="E1",
        difficulty="Easy",
        skill="Direct lookup",
        query="What is the CGPA requirement for TCS?",
        answer="TCS requires 7.5 CGPA.\n\nEvidence:\n- source",
        classification="grounded",
        evidence_count=1,
        evidence_sections=["eligibility"],
    )

    write_evaluation_report([result], output)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["summary"]["by_classification"]["grounded"] == 1
    assert payload["results"][0]["id"] == "E1"


def test_summarize_results_counts_difficulty() -> None:
    result = EvaluationResult(
        id="E1",
        difficulty="Easy",
        skill="Direct lookup",
        query="q",
        answer="a",
        classification="grounded",
        evidence_count=1,
        evidence_sections=[],
    )

    assert summarize_results([result])["by_difficulty"]["Easy"] == 1
