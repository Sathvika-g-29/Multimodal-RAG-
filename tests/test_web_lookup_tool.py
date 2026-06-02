from tools.web_lookup_tool import (
    WebLookupResult,
    duckduckgo_html_search,
    parse_duckduckgo_html,
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


def test_duckduckgo_html_search_returns_snippet(monkeypatch) -> None:
    def fake_post(*args, **kwargs):
        return FakeResponse(
            text="""
            <a rel="nofollow" class="result__a" href="/l/?uddg=https%3A%2F%2Fexample.com">Amazon CEO</a>
            <a class="result__snippet">Andy Jassy is President and CEO of Amazon.</a>
            """
        )

    monkeypatch.setattr("tools.web_lookup_tool.requests.post", fake_post)

    result = duckduckgo_html_search("ceo of amazon")

    assert "Andy Jassy" in result.answer
    assert result.source_url == "https://example.com"
    assert result.status == "html_ok"


def test_web_lookup_uses_html_search(monkeypatch) -> None:
    monkeypatch.setattr(
        "tools.web_lookup_tool.duckduckgo_html_search",
        lambda query, timeout_seconds=8: WebLookupResult(query, "HTML answer", "https://example.com", "html_ok"),
    )

    result = web_lookup("ceo of amazon")

    assert result.answer == "HTML answer"
    assert result.status == "html_ok"
