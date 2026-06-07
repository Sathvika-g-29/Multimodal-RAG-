from tools.web_lookup_tool import (
    WebLookupResult,
    duckduckgo_html_search,
    parse_duckduckgo_html,
    tavily_search,
    web_lookup,
)


class FakeResponse:
    def __init__(self, payload=None, text=""):
        self.payload = payload or {}
        self.text = text

    def raise_for_status(self) -> None:
        return None

    def json(self):
        return self.payload


def test_parse_duckduckgo_html_extracts_result() -> None:
    page = """
    <a rel="nofollow" class="result__a" href="/l/?uddg=https%3A%2F%2Fexample.com">Amazon CEO</a>
    <a class="result__snippet">Andy Jassy is President and CEO of Amazon.</a>
    """

    results = parse_duckduckgo_html(page)

    assert results == [
        {
            "title": "Amazon CEO",
            "snippet": "Andy Jassy is President and CEO of Amazon.",
            "url": "https://example.com",
        }
    ]


def test_parse_duckduckgo_html_handles_href_before_class() -> None:
    page = """
    <div class="result results_links">
      <a href="/l/?uddg=https%3A%2F%2Famazon.com%2Fabout" rel="nofollow" class="result__a">Amazon Leadership</a>
      <span class="result__snippet">Andy Jassy is the CEO of Amazon.</span>
    </div>
    """

    results = parse_duckduckgo_html(page)

    assert results[0]["title"] == "Amazon Leadership"
    assert results[0]["snippet"] == "Andy Jassy is the CEO of Amazon."
    assert results[0]["url"] == "https://amazon.com/about"


def test_duckduckgo_html_search_returns_snippet(monkeypatch) -> None:
    def fake_get(*args, **kwargs):
        return FakeResponse(
            text="""
            <div class="result">
            <a rel="nofollow" class="result__a" href="/l/?uddg=https%3A%2F%2Fexample.com">Amazon CEO</a>
            <div class="result__snippet">Andy Jassy is President and CEO of Amazon.</div>
            </div>
            """
        )

    monkeypatch.setattr("tools.web_lookup_tool.requests.get", fake_get)

    result = duckduckgo_html_search("ceo of amazon")

    assert "Andy Jassy" in result.answer
    assert result.source_url == "https://example.com"
    assert result.status == "html_ok"


def test_duckduckgo_html_search_detects_challenge(monkeypatch) -> None:
    def fake_get(*args, **kwargs):
        return FakeResponse(text='<div class="anomaly-modal">unfortunately, bots use duckduckgo too.</div>')

    monkeypatch.setattr("tools.web_lookup_tool.requests.get", fake_get)

    result = duckduckgo_html_search("ceo of amazon")

    assert result.answer is None
    assert result.status == "duckduckgo_challenge"


def test_tavily_search_returns_answer(monkeypatch) -> None:
    def fake_post(*args, **kwargs):
        return FakeResponse(
            payload={
                "answer": "Andy Jassy is the CEO of Amazon.",
                "results": [{"url": "https://www.aboutamazon.com/about-us/leadership"}],
            }
        )

    monkeypatch.setenv("TAVILY_API_KEY", "test-key")
    monkeypatch.setattr("tools.web_lookup_tool.requests.post", fake_post)

    result = tavily_search("ceo of amazon")

    assert result.answer == "Andy Jassy is the CEO of Amazon."
    assert result.source_url == "https://www.aboutamazon.com/about-us/leadership"
    assert result.status == "tavily_ok"
    assert result.provider == "tavily"


def test_web_lookup_falls_back_to_html_search_without_tavily_key(monkeypatch) -> None:
    monkeypatch.setenv("TAVILY_API_KEY", "")
    monkeypatch.setattr(
        "tools.web_lookup_tool.duckduckgo_html_search",
        lambda query, timeout_seconds=8: WebLookupResult(query, "HTML answer", "https://example.com", "html_ok"),
    )

    result = web_lookup("ceo of amazon")

    assert result.answer == "HTML answer"
    assert result.status == "html_ok"
