from dataclasses import dataclass

from retriever.metadata_filter import metadata_matches


@dataclass(frozen=True)
class RetrievalRequest:
    query: str
    top_k: int
    metadata: dict[str, str | int | float | None]


@dataclass(frozen=True)
class EvidenceChunk:
    text: str
    source: str
    metadata: dict[str, str | int | float | None]


def retrieve_context(request: RetrievalRequest) -> list[EvidenceChunk]:
    from retriever.corpus_loader import load_corpus

    corpus = load_corpus()
    if not corpus:
        return [
            EvidenceChunk(
                text="No indexed placement corpus was found yet. Run the dataset parser first.",
                source="system",
                metadata={"modality": "status"},
            )
        ]

    filtered = [
        chunk
        for chunk in corpus
        if metadata_matches(chunk.metadata, request.metadata)
    ]
    scored = [
        (score_chunk(request.query, chunk), chunk)
        for chunk in filtered
    ]
    ranked = [
        chunk
        for score, chunk in sorted(scored, key=lambda item: item[0], reverse=True)
        if score > 0
    ]

    return ranked[: request.top_k]


def score_chunk(query: str, chunk: EvidenceChunk) -> int:
    query_terms = tokenize(query)
    chunk_terms = tokenize(chunk.text)
    metadata_terms = tokenize(" ".join(str(value) for value in chunk.metadata.values()))

    score = len(query_terms & chunk_terms) * 2
    score += len(query_terms & metadata_terms)

    if chunk.metadata.get("company") and str(chunk.metadata["company"]).casefold() in query.casefold():
        score += 5

    return score


def tokenize(text: str) -> set[str]:
    cleaned = "".join(character if character.isalnum() else " " for character in text.casefold())
    return {token for token in cleaned.split() if len(token) > 1}
