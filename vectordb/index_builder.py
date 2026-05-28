import json
from pathlib import Path

from embeddings.embedder import embed_texts
from retriever.corpus_loader import load_corpus
from vectordb.faiss_store import FaissStore


DEFAULT_INDEX_PATH = "data/extracted/corpus.faiss"
DEFAULT_MANIFEST_PATH = "data/extracted/corpus_manifest.json"


def build_faiss_index(
    corpus_path: str | Path = "data/extracted/corpus.jsonl",
    index_path: str | Path = DEFAULT_INDEX_PATH,
    manifest_path: str | Path = DEFAULT_MANIFEST_PATH,
) -> int:
    corpus = load_corpus(corpus_path)
    if not corpus:
        raise ValueError("No corpus records found. Run scripts.parse_dataset first.")

    vectors = embed_texts([chunk.text for chunk in corpus])
    if not vectors:
        raise ValueError("Embedding model returned no vectors.")

    store = FaissStore(dimension=len(vectors[0]))
    store.add(vectors)

    index_output = Path(index_path)
    manifest_output = Path(manifest_path)
    index_output.parent.mkdir(parents=True, exist_ok=True)
    manifest_output.parent.mkdir(parents=True, exist_ok=True)

    store.save(str(index_output))
    manifest = [
        {
            "text": chunk.text,
            "source": chunk.source,
            "metadata": chunk.metadata,
        }
        for chunk in corpus
    ]
    manifest_output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    return len(corpus)

