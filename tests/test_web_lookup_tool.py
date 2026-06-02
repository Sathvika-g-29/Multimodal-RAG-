from tools.web_lookup_tool import (
    WebLookupResult,
    _parse_capital_target,
    _parse_ceo_target,
    _wikidata_search_entities,
    verified_fallback_lookup,
    web_lookup,
)


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self):
        return self.payload


def test_web_lookup_uses_abstract_text(monkeypatch) -> None:
    monkeypatch.setattr(
        "tools.web_lookup_tool.wikidata_lookup",
        lambda query, timeout_seconds=8: WebLookupResult(query, None, None, "no_wikidata_route"),
    )
    monkeypatch.setattr(
        "tools.web_lookup_tool.wikipedia_lookup",
        lambda query, timeout_seconds=8: WebLookupResult(query, None, None, "no_wikipedia_result"),
    )

    def fake_get(*args, **kwargs):
        return FakeResponse(
            {
                "AbstractText": "Example answer",
                "AbstractURL": "https://example.com",
            }
        )

    monkeypatch.setattr("tools.web_lookup_tool.requests.get", fake_get)

    result = web_lookup("Who is the CEO of TCS?")

    assert result == WebLookupResult(
        query="Who is the CEO of TCS?",
        answer="Example answer",
        source_url="https://example.com",
        status="ok",
    )


def test_web_lookup_handles_empty_result(monkeypatch) -> None:
    monkeypatch.setattr(
        "tools.web_lookup_tool.wikidata_lookup",
        lambda query, timeout_seconds=8: WebLookupResult(query, None, None, "no_wikidata_route"),
    )
    monkeypatch.setattr(
        "tools.web_lookup_tool.wikipedia_lookup",
        lambda query, timeout_seconds=8: WebLookupResult(query, None, None, "no_wikipedia_result"),
    )

    def fake_get(*args, **kwargs):
        return FakeResponse({})

    monkeypatch.setattr("tools.web_lookup_tool.requests.get", fake_get)

    result = web_lookup("unknown")

    assert result.answer is None
    assert result.status == "no_verified_web_answer"


def test_parse_ceo_target() -> None:
    assert _parse_ceo_target("CEO of TCS?") == "TCS"
    assert _parse_ceo_target("Who is the CEO of TCS?") == "TCS"


def test_parse_capital_target() -> None:
    assert _parse_capital_target("capital of France") == "France"


def test_verified_fallback_lookup_handles_tcs_ceo() -> None:
    result = verified_fallback_lookup("ceo of tcs?")

    assert result is not None
    assert "K. Krithivasan" in result.answer
    assert result.status == "ok"


def test_wikidata_search_entities_expands_company_queries(monkeypatch) -> None:
    calls = []

    def fake_search(query, timeout_seconds):
        calls.append(query)
        return [query]

    monkeypatch.setattr("tools.web_lookup_tool._wikidata_search_entity_ids", fake_search)

    results = _wikidata_search_entities("Amazon", "P169", 8)

    assert "Amazon" in calls
    assert "Amazon company" in calls
    assert "Amazon corporation" in calls
    assert "Amazon inc" in calls
    assert results
