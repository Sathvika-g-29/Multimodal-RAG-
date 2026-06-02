import html
import re
from dataclasses import dataclass
from urllib.parse import parse_qs, unquote, urlparse

import requests


DUCKDUCKGO_API_URL = "https://api.duckduckgo.com/"
DUCKDUCKGO_HTML_URL = "https://html.duckduckgo.com/html/"


@dataclass(frozen=True)
class WebLookupResult:
    query: str
    answer: str | None
    source_url: str | None
    status: str
    provider: str = "duckduckgo"


def web_lookup(query: str, timeout_seconds: int = 8) -> WebLookupResult:
    instant_result = duckduckgo_instant_answer(query, timeout_seconds=timeout_seconds)
    if instant_result.answer:
        return instant_result

    search_result = duckduckgo_html_search(query, timeout_seconds=timeout_seconds)
    if search_result.answer:
        return search_result

    return WebLookupResult(
        query=query,
        answer=None,
        source_url=None,
        status=f"{instant_result.status}; {search_result.status}",
    )


def duckduckgo_instant_answer(query: str, timeout_seconds: int = 8) -> WebLookupResult:
    try:
        response = requests.get(
            DUCKDUCKGO_API_URL,
            params={"q": query, "format": "json", "no_html": 1, "skip_disambig": 1},
            headers=_headers(),
            timeout=timeout_seconds,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        return WebLookupResult(query, None, None, f"instant_failed: {exc}")

    payload = response.json()
    answer = payload.get("AbstractText") or payload.get("Answer")
    source_url = payload.get("AbstractURL")
    if not answer:
        for topic in payload.get("RelatedTopics") or []:
            if isinstance(topic, dict) and topic.get("Text"):
                answer = topic["Text"]
                source_url = topic.get("FirstURL")
                break

    return WebLookupResult(
        query=query,
        answer=answer,
        source_url=source_url,
        status="instant_ok" if answer else "instant_no_answer",
    )


def duckduckgo_html_search(query: str, timeout_seconds: int = 8) -> WebLookupResult:
    try:
        response = requests.post(
            DUCKDUCKGO_HTML_URL,
            data={"q": query},
            headers=_headers(),
            timeout=timeout_seconds,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        return WebLookupResult(query, None, None, f"html_failed: {exc}")

    results = parse_duckduckgo_html(response.text)
    if not results:
        return WebLookupResult(query, None, None, "html_no_results")

    first = results[0]
    snippets = " ".join(result["snippet"] for result in results[:3] if result.get("snippet"))
    answer = f"DuckDuckGo search results for '{query}': {snippets}".strip()
    return WebLookupResult(
        query=query,
        answer=answer if snippets else first["title"],
        source_url=first.get("url"),
        status="html_ok",
    )


def parse_duckduckgo_html(page_html: str) -> list[dict[str, str]]:
    result_blocks = re.findall(
        r'<a rel="nofollow" class="result__a" href="(?P<href>.*?)".*?>(?P<title>.*?)</a>.*?'
        r'<a class="result__snippet".*?>(?P<snippet>.*?)</a>',
        page_html,
        flags=re.DOTALL,
    )
    results: list[dict[str, str]] = []
    for href, title, snippet in result_blocks:
        clean_url = _extract_duckduckgo_redirect_url(html.unescape(href))
        results.append(
            {
                "title": _clean_html(title),
                "snippet": _clean_html(snippet),
                "url": clean_url,
            }
        )
    return results


def _extract_duckduckgo_redirect_url(href: str) -> str:
    parsed = urlparse(href)
    uddg = parse_qs(parsed.query).get("uddg")
    if uddg:
        return unquote(uddg[0])
    return href


def _clean_html(value: str) -> str:
    without_tags = re.sub(r"<.*?>", " ", value)
    return " ".join(html.unescape(without_tags).split())


def _headers() -> dict[str, str]:
    return {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0 Safari/537.36"
        )
    }
