import re

from preprocessing.cleaner import normalize_text


HEADING_RE = re.compile(
    r"(?=\b(?:section|chapter|unit)\s+\d+[:.\-\s]|\n[A-Z][A-Za-z0-9 &/()\-]{4,}\n)",
    re.IGNORECASE,
)


def chunk_pdf_text_by_structure(
    text: str,
    chunk_size: int = 1200,
    overlap: int = 150,
) -> list[str]:
    normalized = normalize_text(text)
    if not normalized:
        return []

    sections = [part.strip() for part in HEADING_RE.split(normalized) if part.strip()]
    chunks: list[str] = []
    for section in sections or [normalized]:
        if len(section) <= chunk_size:
            chunks.append(section)
            continue
        chunks.extend(_sliding_chunks(section, chunk_size=chunk_size, overlap=overlap))
    return chunks


def _sliding_chunks(text: str, chunk_size: int, overlap: int) -> list[str]:
    if chunk_size <= overlap:
        raise ValueError("chunk_size must be larger than overlap")

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = end - overlap
    return chunks

