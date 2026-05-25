from retriever.retriever import EvidenceChunk


def generate_answer(query: str, evidence: list[EvidenceChunk]) -> str:
    if not evidence:
        return "I do not have enough retrieved evidence to answer that reliably."

    evidence_text = "\n".join(f"- {chunk.text} [{chunk.source}]" for chunk in evidence)
    return (
        "I need an indexed placement corpus before I can answer with citations.\n\n"
        f"Query: {query}\n\n"
        "Current evidence:\n"
        f"{evidence_text}"
    )

