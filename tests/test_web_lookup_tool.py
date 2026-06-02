from tools.web_lookup_tool import WebLookupResult, tavily_lookup, web_lookup


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self):
        return self.payload


def test_tavily_lookup_uses_configured_provider(monkeypatch) -> None:
    monkeypatch.setenv("TAVILY_API_KEY", "test-key")

    def fake_post(*args, **kwargs):
        return FakeResponse(
            {
                "answer": "Andy Jassy is Amazon's CEO.",
                "results": [{"url": "https://example.com/amazon"}],
            }
        )

    monkeypatch.setattr("tools.web_lookup_tool.requests.post", fake_post)

    result = tavily_lookup("ceo of amazon")

    assert result == WebLookupResult(
        query="ceo of amazon",
        answer="Andy Jassy is Amazon's CEO.",
        source_url="https://example.com/amazon",
        status="ok",
        provider="tavily",
    )


def test_web_lookup_tries_providers_until_answer(monkeypatch) -> None:
    monkeypatch.setattr(
        "tools.web_lookup_tool.tavily_lookup",
        lambda query, timeout_seconds=8: WebLookupResult(query, None, None, "missing_api_key", "tavily"),
    )
    monkeypatch.setattr(
        "tools.web_lookup_tool.brave_lookup",
        lambda query, timeout_seconds=8: WebLookupResult(query, "External answer", "https://example.com", "ok", "brave"),
    )

    result = web_lookup("ceo of amazon")

    assert result.answer == "External answer"
    assert result.provider == "brave"
