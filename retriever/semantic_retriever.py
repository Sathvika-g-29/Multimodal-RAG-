import json
from pathlib import Path

from embeddings.embedder import embed_texts
from retriever.metadata_filter import metadata_matches
from retriever.retriever import EvidenceChunk, RetrievalRequest
from vectordb.faiss_store import FaissStore


DEFAULT_INDEX_PATH = "data/extracted/corpus.faiss"
DEFAULT_MANIFEST_PATH = "data/extracted/corpus_manifest.json"


def semantic_index_exists(
    index_path: str | Path = DEFAULT_INDEX_PATH,
    manifest_path: str | Path = DEFAULT_MANIFEST_PATH,
) -> bool:
    return Path(index_path).exists() and Path(manifest_path).exists()


def retrieve_semantic_context(
    request: RetrievalRequest,
    index_path: str | Path = DEFAULT_INDEX_PATH,
    manifest_path: str | Path = DEFAULT_MANIFEST_PATH,
) -> list[EvidenceChunk]:
    if not semantic_index_exists(index_path, manifest_path):
        return []

    manifest_records = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    store = FaissStore.load(str(index_path))
    query_vector = embed_texts([request.query])[0]

    results = store.search(query_vector, max(request.top_k * 4, request.top_k))
    chunks: list[EvidenceChunk] = []
    for result in results:
        record = manifest_records[result.index]
        chunk = EvidenceChunk(
            text=record["text"],
            source=record["source"],
            metadata=record["metadata"] | {"semantic_score": result.score},
        )
        if metadata_matches(chunk.metadata, request.metadata):
            chunks.append(chunk)
        if len(chunks) >= request.top_k:
            break

    return chunks

