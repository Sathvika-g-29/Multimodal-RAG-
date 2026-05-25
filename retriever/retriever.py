from dataclasses import dataclass

from retriever.reranker import rerank_by_keyword_overlap


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
    """Temporary retrieval boundary until the FAISS index is wired in."""
    _ = request.metadata
    candidates = [
        "No indexed placement corpus was found yet. Upload PDFs/images and run ingestion first."
    ]
    reranked = rerank_by_keyword_overlap(request.query, candidates)[: request.top_k]
    return [
        EvidenceChunk(text=text, source="system", metadata={"modality": "status"})
        for text in reranked
    ]

