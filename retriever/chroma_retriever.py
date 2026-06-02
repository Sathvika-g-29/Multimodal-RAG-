from pathlib import Path

from retriever.retriever import EvidenceChunk, RetrievalRequest
from vectordb.chroma_store import DEFAULT_CHROMA_PATH, DEFAULT_COLLECTION, query_chroma


def chroma_index_exists(persist_path: str = DEFAULT_CHROMA_PATH) -> bool:
    return Path(persist_path).exists() and any(Path(persist_path).iterdir())


def retrieve_chroma_context(
    request: RetrievalRequest,
    persist_path: str = DEFAULT_CHROMA_PATH,
    collection_name: str = DEFAULT_COLLECTION,
) -> list[EvidenceChunk]:
    if not chroma_index_exists(persist_path):
        return []

    from embeddings.embedder import embed_texts

    query_embedding = embed_texts([request.query])[0]
    return query_chroma(
        query_embedding=query_embedding,
        top_k=request.top_k,
        metadata=request.metadata,
        persist_path=persist_path,
        collection_name=collection_name,
    )
