from dataclasses import dataclass

from retriever.retriever import EvidenceChunk, tokenize


@dataclass(frozen=True)
class GuardrailReport:
    matrix_quadrant: str
    look_back_ratio: float
    supported_claims: int
    total_claims: int
    conflict_found: bool
    refutation_note: str | None
    self_consistency: str
    decision: str


def apply_guardrails(answer: str, evidence: list[EvidenceChunk]) -> str:
    report = system2_review(answer, evidence)
    if report.decision == "refuse":
        return "I do not have enough retrieved evidence to answer that reliably."

    notes = [
        (
            f"Grounding check: {report.decision}; "
            f"matrix={report.matrix_quadrant}; "
            f"look-back ratio={report.look_back_ratio:.2f}; "
            f"supported claims={report.supported_claims}/{report.total_claims}."
        )
    ]
    if report.refutation_note:
        notes.append(f"Refutation check: {report.refutation_note}")
    notes.append(f"Self-consistency: {report.self_consistency}.")

    return f"{answer}\n\n" + "\n".join(notes)


def system2_review(answer: str, evidence: list[EvidenceChunk]) -> GuardrailReport:
    conflict_found = any(chunk.metadata.get("conflict") for chunk in evidence)
    supported_claims, total_claims = count_supported_claims(answer, evidence)
    ratio = supported_claims / total_claims if total_claims else 0.0
    matrix_quadrant = evidence_support_matrix(bool(evidence), ratio)
    refutation_note = refutation_check(evidence)
    self_consistency = self_consistency_check(evidence)

    if not evidence:
        decision = "refuse"
    elif conflict_found:
        decision = "conflict-aware"
    elif ratio >= 0.35:
        decision = "grounded"
    else:
        decision = "needs-review"

    return GuardrailReport(
        matrix_quadrant=matrix_quadrant,
        look_back_ratio=ratio,
        supported_claims=supported_claims,
        total_claims=total_claims,
        conflict_found=conflict_found,
        refutation_note=refutation_note,
        self_consistency=self_consistency,
        decision=decision,
    )


def evidence_support_matrix(evidence_present: bool, look_back_ratio: float) -> str:
    answer_supported = look_back_ratio >= 0.35
    if evidence_present and answer_supported:
        return "evidence_present_answer_supported"
    if evidence_present and not answer_supported:
        return "evidence_present_answer_weakly_supported"
    if not evidence_present and answer_supported:
        return "no_evidence_possible_memory_answer"
    return "no_evidence_no_answer"


def count_supported_claims(answer: str, evidence: list[EvidenceChunk]) -> tuple[int, int]:
    claims = split_claims(answer)
    if not claims:
        return 0, 0

    evidence_terms = tokenize(" ".join(chunk.text for chunk in evidence))
    supported = 0
    for claim in claims:
        claim_terms = tokenize(claim)
        if not claim_terms:
            continue
        overlap = claim_terms & evidence_terms
        if len(overlap) / max(len(claim_terms), 1) >= 0.25:
            supported += 1
    return supported, len(claims)


def split_claims(answer: str) -> list[str]:
    cleaned = answer.replace("\n", " ")
    rough_claims = []
    for part in cleaned.split("."):
        claim = part.strip()
        if claim and not claim.casefold().startswith("grounding check"):
            rough_claims.append(claim)
    return rough_claims


def refutation_check(evidence: list[EvidenceChunk]) -> str | None:
    conflict_chunks = [chunk for chunk in evidence if chunk.metadata.get("conflict")]
    if not conflict_chunks:
        return None

    authorities = sorted(
        {
            str(chunk.metadata.get("source_authority", "unknown"))
            for chunk in conflict_chunks
        }
    )
    companies = sorted(
        {
            str(chunk.metadata.get("company", "unknown"))
            for chunk in conflict_chunks
        }
    )
    return (
        f"conflicting evidence found for {', '.join(companies)} "
        f"from {', '.join(authorities)} sources"
    )


def self_consistency_check(evidence: list[EvidenceChunk]) -> str:
    if not evidence:
        return "no retrieved evidence"

    sections = {str(chunk.metadata.get("section", "unknown")) for chunk in evidence}
    companies = {str(chunk.metadata.get("company", "")) for chunk in evidence if chunk.metadata.get("company")}
    if len(sections) >= 2:
        return f"cross-checked across {len(sections)} sections"
    if len(companies) == 1 and len(evidence) >= 2:
        return f"multiple chunks agree for {next(iter(companies))}"
    return "single-source evidence"

