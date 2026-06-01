from retriever.retriever import EvidenceChunk


def generate_answer(query: str, evidence: list[EvidenceChunk]) -> str:
    from reasoning.guardrails import apply_guardrails
    from reasoning.rule_engine import answer_with_rules
    from retriever.corpus_loader import load_corpus

    rule_answer = answer_with_rules(query, load_corpus())
    if rule_answer:
        answer = _format_answer(rule_answer.text, rule_answer.evidence)
        if not rule_answer.evidence:
            return answer
        return apply_guardrails(answer, rule_answer.evidence)

    if not evidence:
        return "I do not have enough retrieved evidence to answer that reliably."

    conflict_chunks = [chunk for chunk in evidence if chunk.metadata.get("conflict")]
    evidence_text = "\n".join(
        f"- {chunk.text} [{chunk.source}; section={chunk.metadata.get('section', 'unknown')}]"
        for chunk in evidence
    )

    if conflict_chunks:
        answer = (
            "I found conflicting placement records, so this should be verified with the official placement cell.\n\n"
            f"Query: {query}\n\n"
            "Retrieved evidence:\n"
            f"{evidence_text}"
        )
        return apply_guardrails(answer, evidence)

    answer = (
        f"Query: {query}\n\n"
        "Retrieved evidence:\n"
        f"{evidence_text}"
    )
    return apply_guardrails(answer, evidence)


def _format_answer(answer: str, evidence: list[EvidenceChunk]) -> str:
    if not evidence:
        return answer

    evidence_text = "\n".join(
        f"- {chunk.text} [{chunk.source}; section={chunk.metadata.get('section', 'unknown')}]"
        for chunk in evidence[:5]
    )
    return f"{answer}\n\nEvidence:\n{evidence_text}"
