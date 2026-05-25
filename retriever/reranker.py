def rerank_by_keyword_overlap(query: str, documents: list[str]) -> list[str]:
    query_terms = set(query.casefold().split())

    def score(document: str) -> int:
        return len(query_terms.intersection(document.casefold().split()))

    return sorted(documents, key=score, reverse=True)

