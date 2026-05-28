from dataclasses import dataclass

import faiss
import numpy as np


@dataclass
class FaissSearchResult:
    index: int
    score: float


class FaissStore:
    def __init__(self, dimension: int) -> None:
        self.index = faiss.IndexFlatIP(dimension)

    def add(self, vectors: list[list[float]]) -> None:
        array = np.array(vectors, dtype="float32")
        self.index.add(array)

    def search(self, query_vector: list[float], top_k: int) -> list[FaissSearchResult]:
        query = np.array([query_vector], dtype="float32")
        scores, indexes = self.index.search(query, top_k)
        return [
            FaissSearchResult(index=int(index), score=float(score))
            for index, score in zip(indexes[0], scores[0])
            if index >= 0
        ]

    def save(self, path: str) -> None:
        faiss.write_index(self.index, path)

    @classmethod
    def load(cls, path: str) -> "FaissStore":
        index = faiss.read_index(path)
        store = cls(index.d)
        store.index = index
        return store

