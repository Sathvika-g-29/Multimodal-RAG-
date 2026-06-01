from tools.web_lookup_tool import WebLookupResult, web_lookup


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self):
        return self.payload


def test_web_lookup_uses_abstract_text(monkeypatch) -> None:
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
    def fake_get(*args, **kwargs):
        return FakeResponse({})

    monkeypatch.setattr("tools.web_lookup_tool.requests.get", fake_get)

    result = web_lookup("unknown")

    assert result.answer is None
    assert result.status == "no_verified_web_answer"
