from dataclasses import dataclass

import requests


DUCKDUCKGO_API_URL = "https://api.duckduckgo.com/"


@dataclass(frozen=True)
class WebLookupResult:
    query: str
    answer: str | None
    source_url: str | None
    status: str


def web_lookup(query: str, timeout_seconds: int = 8) -> WebLookupResult:
    try:
        response = requests.get(
            DUCKDUCKGO_API_URL,
            params={
                "q": query,
                "format": "json",
                "no_html": 1,
                "skip_disambig": 1,
            },
            timeout=timeout_seconds,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        return WebLookupResult(
            query=query,
            answer=None,
            source_url=None,
            status=f"web_lookup_failed: {exc}",
        )

    payload = response.json()
    answer = payload.get("AbstractText") or payload.get("Answer")
    source_url = payload.get("AbstractURL") or payload.get("AnswerType")

    if not answer:
        related_topics = payload.get("RelatedTopics") or []
        for topic in related_topics:
            if isinstance(topic, dict) and topic.get("Text"):
                answer = topic["Text"]
                source_url = topic.get("FirstURL")
                break

    if not answer:
        return WebLookupResult(
            query=query,
            answer=None,
            source_url=None,
            status="no_verified_web_answer",
        )

    return WebLookupResult(
        query=query,
        answer=answer,
        source_url=source_url,
        status="ok",
    )

