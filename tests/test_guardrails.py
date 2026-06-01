from reasoning.guardrails import evidence_support_matrix, refutation_check, system2_review
from retriever.retriever import EvidenceChunk


def test_evidence_support_matrix_marks_grounded() -> None:
    assert evidence_support_matrix(True, 0.8) == "evidence_present_answer_supported"


def test_system2_review_detects_supported_answer() -> None:
    evidence = [
        EvidenceChunk(
            text="Amazon eligibility: minimum CGPA 6.4, maximum backlogs 1.",
            source="eligibility_row",
            metadata={"section": "eligibility", "company": "Amazon"},
        )
    ]

    report = system2_review("Amazon minimum CGPA is 6.4.", evidence)

    assert report.decision == "grounded"
    assert report.look_back_ratio > 0


def test_refutation_check_detects_conflict_metadata() -> None:
    evidence = [
        EvidenceChunk(
            text="Amazon official CGPA cutoff is 6.4.",
            source="conflict_record",
            metadata={
                "section": "conflict",
                "company": "Amazon",
                "conflict": True,
                "source_authority": "official",
            },
        )
    ]

    assert "conflicting evidence" in refutation_check(evidence)
