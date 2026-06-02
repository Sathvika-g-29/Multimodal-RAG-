import os
from dataclasses import dataclass

import requests


TAVILY_API_URL = "https://api.tavily.com/search"
BRAVE_API_URL = "https://api.search.brave.com/res/v1/web/search"
SERPAPI_URL = "https://serpapi.com/search.json"
DUCKDUCKGO_API_URL = "https://api.duckduckgo.com/"
WIKIPEDIA_API_URL = "https://en.wikipedia.org/w/api.php"


@dataclass(frozen=True)
class WebLookupResult:
    query: str
    answer: str | None
    source_url: str | None
    status: str
    provider: str = "none"


def web_lookup(query: str, timeout_seconds: int = 8) -> WebLookupResult:
    providers = [
        tavily_lookup,
        brave_lookup,
        serpapi_lookup,
        wikipedia_lookup,
        duckduckgo_lookup,
    ]

    statuses: list[str] = []
    for provider in providers:
        result = provider(query, timeout_seconds=timeout_seconds)
        if result.answer:
            return result
        statuses.append(f"{result.provider}:{result.status}")

    return WebLookupResult(
        query=query,
        answer=None,
        source_url=None,
        status="; ".join(statuses) or "no_provider_answer",
        provider="web_tool",
    )


def tavily_lookup(query: str, timeout_seconds: int = 8) -> WebLookupResult:
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return WebLookupResult(query, None, None, "missing_api_key", "tavily")

    try:
        response = requests.post(
            TAVILY_API_URL,
            json={
                "api_key": api_key,
                "query": query,
                "search_depth": "basic",
                "include_answer": True,
                "max_results": 5,
            },
            timeout=timeout_seconds,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        return WebLookupResult(query, None, None, f"request_failed: {exc}", "tavily")

    payload = response.json()
    answer = payload.get("answer")
    results = payload.get("results") or []
    source_url = results[0].get("url") if results else None
    if not answer and results:
        answer = _answer_from_results(query, results)
    return WebLookupResult(query, answer, source_url, "ok" if answer else "no_answer", "tavily")


def brave_lookup(query: str, timeout_seconds: int = 8) -> WebLookupResult:
    api_key = os.getenv("BRAVE_SEARCH_API_KEY")
    if not api_key:
        return WebLookupResult(query, None, None, "missing_api_key", "brave")

    try:
        response = requests.get(
            BRAVE_API_URL,
            params={"q": query, "count": 5},
            headers={"X-Subscription-Token": api_key},
            timeout=timeout_seconds,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        return WebLookupResult(query, None, None, f"request_failed: {exc}", "brave")

    web_results = response.json().get("web", {}).get("results", [])
    answer = _answer_from_results(query, web_results)
    source_url = web_results[0].get("url") if web_results else None
    return WebLookupResult(query, answer, source_url, "ok" if answer else "no_answer", "brave")


def serpapi_lookup(query: str, timeout_seconds: int = 8) -> WebLookupResult:
    api_key = os.getenv("SERPAPI_API_KEY")
    if not api_key:
        return WebLookupResult(query, None, None, "missing_api_key", "serpapi")

    try:
        response = requests.get(
            SERPAPI_URL,
            params={"q": query, "api_key": api_key, "engine": "google"},
            timeout=timeout_seconds,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        return WebLookupResult(query, None, None, f"request_failed: {exc}", "serpapi")

    payload = response.json()
    answer_box = payload.get("answer_box") or {}
    answer = answer_box.get("answer") or answer_box.get("snippet")
    source_url = answer_box.get("link")
    organic_results = payload.get("organic_results") or []
    if not answer and organic_results:
        answer = _answer_from_results(query, organic_results)
        source_url = organic_results[0].get("link")
    return WebLookupResult(query, answer, source_url, "ok" if answer else "no_answer", "serpapi")


def wikipedia_lookup(query: str, timeout_seconds: int = 8) -> WebLookupResult:
    try:
        search_response = requests.get(
            WIKIPEDIA_API_URL,
            params={
                "action": "query",
                "list": "search",
                "srsearch": query,
                "format": "json",
                "srlimit": 1,
            },
            timeout=timeout_seconds,
        )
        search_response.raise_for_status()
        search_results = search_response.json().get("query", {}).get("search", [])
        if not search_results:
            return WebLookupResult(query, None, None, "no_result", "wikipedia")

        title = search_results[0]["title"]
        summary_response = requests.get(
            f"https://en.wikipedia.org/api/rest_v1/page/summary/{title.replace(' ', '_')}",
            timeout=timeout_seconds,
        )
        summary_response.raise_for_status()
    except requests.RequestException as exc:
        return WebLookupResult(query, None, None, f"request_failed: {exc}", "wikipedia")

    payload = summary_response.json()
    answer = payload.get("extract")
    source_url = payload.get("content_urls", {}).get("desktop", {}).get("page")
    return WebLookupResult(query, answer, source_url, "ok" if answer else "no_summary", "wikipedia")


def duckduckgo_lookup(query: str, timeout_seconds: int = 8) -> WebLookupResult:
    try:
        response = requests.get(
            DUCKDUCKGO_API_URL,
            params={"q": query, "format": "json", "no_html": 1, "skip_disambig": 1},
            timeout=timeout_seconds,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        return WebLookupResult(query, None, None, f"request_failed: {exc}", "duckduckgo")

    payload = response.json()
    answer = payload.get("AbstractText") or payload.get("Answer")
    source_url = payload.get("AbstractURL")
    if not answer:
        for topic in payload.get("RelatedTopics") or []:
            if isinstance(topic, dict) and topic.get("Text"):
                answer = topic["Text"]
                source_url = topic.get("FirstURL")
                break
    return WebLookupResult(query, answer, source_url, "ok" if answer else "no_answer", "duckduckgo")


def _answer_from_results(query: str, results: list[dict]) -> str | None:
    snippets = []
    for result in results[:3]:
        snippet = result.get("snippet") or result.get("description") or result.get("content")
        title = result.get("title")
        if snippet:
            snippets.append(f"{title}: {snippet}" if title else snippet)
    if not snippets:
        return None
    return f"Web results for '{query}': " + " ".join(snippets)
