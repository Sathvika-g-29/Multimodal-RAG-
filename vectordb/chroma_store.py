from pathlib import Path

from retriever.retriever import EvidenceChunk


DEFAULT_CHROMA_PATH = "data/extracted/chroma"
DEFAULT_COLLECTION = "placement_corpus"


def get_chroma_client(persist_path: str = DEFAULT_CHROMA_PATH):
    try:
        import chromadb
    except ImportError as exc:
        raise RuntimeError("Install chromadb to use the persistent Chroma vector store.") from exc

    Path(persist_path).mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=persist_path)


def reset_collection(
    persist_path: str = DEFAULT_CHROMA_PATH,
    collection_name: str = DEFAULT_COLLECTION,
):
    client = get_chroma_client(persist_path)
    try:
        client.delete_collection(collection_name)
    except Exception:
        pass
    return client.get_or_create_collection(collection_name)


def get_collection(
    persist_path: str = DEFAULT_CHROMA_PATH,
    collection_name: str = DEFAULT_COLLECTION,
):
    client = get_chroma_client(persist_path)
    return client.get_or_create_collection(collection_name)


def add_chunks_to_chroma(
    chunks: list[EvidenceChunk],
    embeddings: list[list[float]],
    persist_path: str = DEFAULT_CHROMA_PATH,
    collection_name: str = DEFAULT_COLLECTION,
) -> int:
    if len(chunks) != len(embeddings):
        raise ValueError("chunks and embeddings must have the same length")

    collection = reset_collection(persist_path, collection_name)
    ids = [f"{index}-{abs(hash(chunk.text))}" for index, chunk in enumerate(chunks)]
    collection.add(
        ids=ids,
        documents=[chunk.text for chunk in chunks],
        embeddings=embeddings,
        metadatas=[
            _metadata_for_chroma(chunk.metadata | {"source": chunk.source})
            for chunk in chunks
        ],
    )
    return len(chunks)


def query_chroma(
    query_embedding: list[float],
    top_k: int,
    metadata: dict[str, str | int | float | None],
    persist_path: str = DEFAULT_CHROMA_PATH,
    collection_name: str = DEFAULT_COLLECTION,
) -> list[EvidenceChunk]:
    collection = get_collection(persist_path, collection_name)
    where = _where_filter(metadata)
    kwargs = {
        "query_embeddings": [query_embedding],
        "n_results": top_k,
    }
    if where:
        kwargs["where"] = where

    result = collection.query(**kwargs)
    documents = result.get("documents", [[]])[0]
    metadatas = result.get("metadatas", [[]])[0]
    chunks: list[EvidenceChunk] = []
    for text, item_metadata in zip(documents, metadatas):
        source = str(item_metadata.pop("source", "chroma"))
        chunks.append(EvidenceChunk(text=text, source=source, metadata=item_metadata))
    return chunks


def _metadata_for_chroma(metadata: dict[str, str | int | float | bool | None]) -> dict[str, str | int | float | bool]:
    return {
        key: value
        for key, value in metadata.items()
        if value is not None and isinstance(value, (str, int, float, bool))
    }


def _where_filter(metadata: dict[str, str | int | float | None]) -> dict[str, object] | None:
    cleaned = {
        key: value
        for key, value in metadata.items()
        if value is not None and isinstance(value, (str, int, float))
    }
    if not cleaned:
        return None
    if len(cleaned) == 1:
        return cleaned
    return {"$and": [{key: value} for key, value in cleaned.items()]}
