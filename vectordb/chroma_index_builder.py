from pathlib import Path

from embeddings.embedder import embed_texts
from retriever.corpus_loader import load_corpus
from vectordb.chroma_store import DEFAULT_CHROMA_PATH, DEFAULT_COLLECTION, add_chunks_to_chroma


def build_chroma_index(
    corpus_path: str | Path = "data/extracted/corpus.jsonl",
    persist_path: str = DEFAULT_CHROMA_PATH,
    collection_name: str = DEFAULT_COLLECTION,
    reset: bool = True,
) -> int:
    corpus = load_corpus(corpus_path)
    if not corpus:
        raise ValueError("No corpus records found. Run scripts.parse_dataset first.")

    embeddings = embed_texts([chunk.text for chunk in corpus])
    return add_chunks_to_chroma(
        chunks=corpus,
        embeddings=embeddings,
        persist_path=persist_path,
        collection_name=collection_name,
        reset=reset,
    )
