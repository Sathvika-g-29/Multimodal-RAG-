from retriever.retriever import EvidenceChunk


def generate_answer(query: str, evidence: list[EvidenceChunk]) -> str:
    if not evidence:
        return "I do not have enough retrieved evidence to answer that reliably."

    conflict_chunks = [chunk for chunk in evidence if chunk.metadata.get("conflict")]
    evidence_text = "\n".join(
        f"- {chunk.text} [{chunk.source}; section={chunk.metadata.get('section', 'unknown')}]"
        for chunk in evidence
    )

    if conflict_chunks:
        return (
            "I found conflicting placement records, so this should be verified with the official placement cell.\n\n"
            f"Query: {query}\n\n"
            "Retrieved evidence:\n"
            f"{evidence_text}"
        )

    return (
        f"Query: {query}\n\n"
        "Retrieved evidence:\n"
        f"{evidence_text}"
    )
