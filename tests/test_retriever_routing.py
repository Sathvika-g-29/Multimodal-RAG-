from retriever.retriever import RetrievalRequest, retrieve_context, should_skip_corpus_retrieval


def test_current_info_queries_skip_corpus_retrieval() -> None:
    assert should_skip_corpus_retrieval("Who is the CEO of TCS?")


def test_retrieve_context_skips_current_info_query() -> None:
    evidence = retrieve_context(RetrievalRequest(query="Who is the CEO of TCS?", top_k=5, metadata={}))

    assert evidence == []
