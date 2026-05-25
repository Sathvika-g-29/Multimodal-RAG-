from dataclasses import dataclass


@dataclass(frozen=True)
class TextChunk:
    text: str
    metadata: dict[str, str | int | float | None]


def chunk_text(
    text: str,
    metadata: dict[str, str | int | float | None],
    chunk_size: int = 900,
    overlap: int = 120,
) -> list[TextChunk]:
    if chunk_size <= overlap:
        raise ValueError("chunk_size must be larger than overlap")

    chunks: list[TextChunk] = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(TextChunk(text=chunk, metadata=metadata))
        start = end - overlap

    return chunks

