from collections.abc import Iterable


def deduplicate_texts(texts: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []

    for text in texts:
        normalized_key = text.casefold().strip()
        if normalized_key and normalized_key not in seen:
            seen.add(normalized_key)
            unique.append(text)

    return unique

