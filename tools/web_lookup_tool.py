import html
import os
import re
from dataclasses import dataclass
from urllib.parse import parse_qs, unquote, urlparse

import requests
from dotenv import load_dotenv


DUCKDUCKGO_HTML_URL = "https://html.duckduckgo.com/html/"
TAVILY_SEARCH_URL = "https://api.tavily.com/search"


@dataclass(frozen=True)
class WebLookupResult:
    query: str
    answer: str | None
    source_url: str | None
    status: str
    provider: str = "duckduckgo"


def web_lookup(query: str, timeout_seconds: int = 8) -> WebLookupResult:
    tavily_result = tavily_search(query, timeout_seconds=timeout_seconds)
    if tavily_result.status != "tavily_missing_api_key":
        return tavily_result
    return duckduckgo_html_search(query, timeout_seconds=timeout_seconds)


def tavily_search(query: str, timeout_seconds: int = 8) -> WebLookupResult:
    load_dotenv()
    api_key = os.getenv("TAVILY_API_KEY", "").strip()
    if not api_key:
        return WebLookupResult(query, None, None, "tavily_missing_api_key", provider="tavily")

    payload = {
        "api_key": api_key,
        "query": query,
        "search_depth": "basic",
        "include_answer": True,
        "max_results": 3,
    }
    try:
        response = requests.post(TAVILY_SEARCH_URL, json=payload, timeout=timeout_seconds)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        return WebLookupResult(query, None, None, f"tavily_failed: {exc}", provider="tavily")
    except ValueError as exc:
        return WebLookupResult(query, None, None, f"tavily_bad_json: {exc}", provider="tavily")

    answer = _clean_tavily_answer(data)
    source_url = _first_tavily_source_url(data)
    if not answer:
        return WebLookupResult(query, None, source_url, "tavily_no_answer", provider="tavily")

    return WebLookupResult(query, answer, source_url, "tavily_ok", provider="tavily")


def duckduckgo_html_search(query: str, timeout_seconds: int = 8) -> WebLookupResult:
    try:
        response = requests.get(
            DUCKDUCKGO_HTML_URL,
            params={"q": query},
            headers=_headers(),
            timeout=timeout_seconds,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        return WebLookupResult(query, None, None, f"html_failed: {exc}")

    if _is_duckduckgo_challenge(response.text):
        return WebLookupResult(query, None, None, "duckduckgo_challenge", provider="duckduckgo")

    results = parse_duckduckgo_html(response.text)
    if not results:
        return WebLookupResult(query, None, None, "html_no_results", provider="duckduckgo")

    first = results[0]
    snippets = " ".join(result["snippet"] for result in results[:3] if result.get("snippet"))
    answer = f"DuckDuckGo search results for '{query}': {snippets}".strip()
    return WebLookupResult(
        query=query,
        answer=answer if snippets else first["title"],
        source_url=first.get("url"),
        status="html_ok",
        provider="duckduckgo",
    )


def _clean_tavily_answer(data: dict) -> str | None:
    direct_answer = str(data.get("answer") or "").strip()
    if direct_answer:
        return direct_answer

    snippets = []
    for result in data.get("results", [])[:3]:
        content = str(result.get("content") or "").strip()
        if content:
            snippets.append(content)
    return " ".join(snippets) if snippets else None


def _first_tavily_source_url(data: dict) -> str | None:
    for result in data.get("results", []):
        url = str(result.get("url") or "").strip()
        if url:
            return url
    return None


def parse_duckduckgo_html(page_html: str) -> list[dict[str, str]]:
    results: list[dict[str, str]] = []
    blocks = re.split(
        r'<div[^>]+class="(?=[^"]*(?:\bresult\b|results_links|web-result))[^"]*"[^>]*>',
        page_html,
    )
    for block in blocks:
        link = _find_result_link(block)
        if not link:
            continue

        snippet_match = re.search(
            r'<(?:a|div|span)[^>]+class="[^"]*(?:result__snippet|result-snippet)[^"]*"[^>]*>(?P<snippet>.*?)</(?:a|div|span)>',
            block,
            flags=re.DOTALL,
        )
        title = _clean_html(link["title"])
        snippet = _clean_html(snippet_match.group("snippet")) if snippet_match else title
        clean_url = _extract_duckduckgo_redirect_url(html.unescape(link["href"]))
        results.append({"title": title, "snippet": snippet, "url": clean_url})

    if results:
        return results

    for link in _find_all_result_links(page_html):
        title = _clean_html(link["title"])
        clean_url = _extract_duckduckgo_redirect_url(html.unescape(link["href"]))
        results.append({"title": title, "snippet": title, "url": clean_url})
    return results


def _find_result_link(block: str) -> dict[str, str] | None:
    links = _find_all_result_links(block)
    return links[0] if links else None


def _find_all_result_links(page_html: str) -> list[dict[str, str]]:
    links: list[dict[str, str]] = []
    for match in re.finditer(r"<a(?P<attrs>[^>]*)>(?P<title>.*?)</a>", page_html, flags=re.DOTALL):
        attrs = match.group("attrs")
        class_match = re.search(r'class=["\'](?P<class>.*?)["\']', attrs, flags=re.DOTALL)
        if not class_match:
            continue

        classes = class_match.group("class")
        if "result__a" not in classes and "result-link" not in classes:
            continue

        href_match = re.search(r'href=["\'](?P<href>.*?)["\']', attrs, flags=re.DOTALL)
        if not href_match:
            continue

        links.append({"href": href_match.group("href"), "title": match.group("title")})
    return links


def _extract_duckduckgo_redirect_url(href: str) -> str:
    parsed = urlparse(href)
    uddg = parse_qs(parsed.query).get("uddg")
    if uddg:
        return unquote(uddg[0])
    return href


def _clean_html(value: str) -> str:
    without_tags = re.sub(r"<.*?>", " ", value)
    return " ".join(html.unescape(without_tags).split())


def _is_duckduckgo_challenge(page_html: str) -> bool:
    normalized = page_html.casefold()
    return "anomaly-modal" in normalized or "unfortunately, bots use duckduckgo too" in normalized


def _headers() -> dict[str, str]:
    return {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0 Safari/537.36"
        )
    }
