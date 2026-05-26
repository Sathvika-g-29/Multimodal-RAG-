import json
from pathlib import Path

from retriever.retriever import EvidenceChunk


def load_corpus(path: str | Path = "data/extracted/corpus.jsonl") -> list[EvidenceChunk]:
    corpus_path = Path(path)

    if not corpus_path.exists():
        return []

    chunks = []
    with corpus_path.open("r", encoding="utf-8") as file:
        for line in file:
            if not line.strip():
                continue

            record = json.loads(line)
            chunks.append(
                EvidenceChunk(
                    text=record["text"],
                    source=record["source_type"],
                    metadata=record["metadata"],
                )
            )

    return chunks