from vectordb.faiss_store import FaissStore


def test_faiss_store_searches_added_vectors() -> None:
    store = FaissStore(dimension=3)
    store.add([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])

    results = store.search([1.0, 0.0, 0.0], top_k=1)

    assert results[0].index == 0
    assert results[0].score == 1.0


def test_faiss_store_round_trip(tmp_path) -> None:
    index_path = tmp_path / "test.faiss"
    store = FaissStore(dimension=2)
    store.add([[0.0, 1.0]])
    store.save(str(index_path))

    loaded = FaissStore.load(str(index_path))
    results = loaded.search([0.0, 1.0], top_k=1)

    assert results[0].index == 0
