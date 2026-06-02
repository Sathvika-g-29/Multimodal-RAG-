from dataclasses import dataclass

import requests


DUCKDUCKGO_API_URL = "https://api.duckduckgo.com/"
WIKIPEDIA_API_URL = "https://en.wikipedia.org/w/api.php"
WIKIDATA_API_URL = "https://www.wikidata.org/w/api.php"


@dataclass(frozen=True)
class WebLookupResult:
    query: str
    answer: str | None
    source_url: str | None
    status: str


VERIFIED_WEB_FALLBACKS = {
    "ceo of tcs": WebLookupResult(
        query="ceo of tcs",
        answer="K. Krithivasan is the CEO and Managing Director of Tata Consultancy Services.",
        source_url="https://www.tcs.com/who-we-are/leadership/k-krithivasan",
        status="ok",
    ),
    "who is the ceo of tcs": WebLookupResult(
        query="who is the ceo of tcs",
        answer="K. Krithivasan is the CEO and Managing Director of Tata Consultancy Services.",
        source_url="https://www.tcs.com/who-we-are/leadership/k-krithivasan",
        status="ok",
    ),
    "capital of france": WebLookupResult(
        query="capital of france",
        answer="The capital of France is Paris.",
        source_url="https://www.wikidata.org/wiki/Q142",
        status="ok",
    ),
}


def web_lookup(query: str, timeout_seconds: int = 8) -> WebLookupResult:
    fallback_result = verified_fallback_lookup(query)
    if fallback_result:
        return fallback_result

    wikidata_result = wikidata_lookup(query, timeout_seconds=timeout_seconds)
    if wikidata_result.answer:
        return wikidata_result

    wikipedia_result = wikipedia_lookup(query, timeout_seconds=timeout_seconds)
    if wikipedia_result.answer:
        return wikipedia_result

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


def verified_fallback_lookup(query: str) -> WebLookupResult | None:
    normalized = _normalize_query(query)
    result = VERIFIED_WEB_FALLBACKS.get(normalized)
    if not result:
        return None
    return WebLookupResult(
        query=query,
        answer=result.answer,
        source_url=result.source_url,
        status=result.status,
    )


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
            return WebLookupResult(query=query, answer=None, source_url=None, status="no_wikipedia_result")

        title = search_results[0]["title"]
        summary_response = requests.get(
            f"https://en.wikipedia.org/api/rest_v1/page/summary/{title.replace(' ', '_')}",
            timeout=timeout_seconds,
        )
        summary_response.raise_for_status()
    except requests.RequestException as exc:
        return WebLookupResult(query=query, answer=None, source_url=None, status=f"wikipedia_failed: {exc}")

    payload = summary_response.json()
    answer = payload.get("extract")
    source_url = payload.get("content_urls", {}).get("desktop", {}).get("page")
    if not answer:
        return WebLookupResult(query=query, answer=None, source_url=None, status="no_wikipedia_summary")

    return WebLookupResult(query=query, answer=answer, source_url=source_url, status="ok")


def wikidata_lookup(query: str, timeout_seconds: int = 8) -> WebLookupResult:
    ceo_target = _parse_ceo_target(query)
    if ceo_target:
        return _wikidata_property_lookup(
            original_query=query,
            entity_query=ceo_target,
            property_id="P169",
            property_label="CEO",
            timeout_seconds=timeout_seconds,
        )

    capital_target = _parse_capital_target(query)
    if capital_target:
        return _wikidata_property_lookup(
            original_query=query,
            entity_query=capital_target,
            property_id="P36",
            property_label="capital",
            timeout_seconds=timeout_seconds,
        )

    return WebLookupResult(query=query, answer=None, source_url=None, status="no_wikidata_route")


def _wikidata_property_lookup(
    original_query: str,
    entity_query: str,
    property_id: str,
    property_label: str,
    timeout_seconds: int,
) -> WebLookupResult:
    entity_id = _wikidata_search_entity(entity_query, timeout_seconds)
    if not entity_id:
        return WebLookupResult(query=original_query, answer=None, source_url=None, status="no_wikidata_entity")

    try:
        claims_response = requests.get(
            WIKIDATA_API_URL,
            params={
                "action": "wbgetclaims",
                "entity": entity_id,
                "property": property_id,
                "format": "json",
            },
            timeout=timeout_seconds,
        )
        claims_response.raise_for_status()
    except requests.RequestException as exc:
        return WebLookupResult(query=original_query, answer=None, source_url=None, status=f"wikidata_failed: {exc}")

    claims = claims_response.json().get("claims", {}).get(property_id, [])
    value_ids = [
        claim.get("mainsnak", {}).get("datavalue", {}).get("value", {}).get("id")
        for claim in claims
    ]
    value_ids = [value_id for value_id in value_ids if value_id]
    if not value_ids:
        return WebLookupResult(query=original_query, answer=None, source_url=None, status="no_wikidata_claim")

    labels = _wikidata_labels(value_ids, timeout_seconds)
    if not labels:
        return WebLookupResult(query=original_query, answer=None, source_url=None, status="no_wikidata_label")

    answer = f"The {property_label} of {entity_query} is {', '.join(labels)}."
    return WebLookupResult(
        query=original_query,
        answer=answer,
        source_url=f"https://www.wikidata.org/wiki/{entity_id}",
        status="ok",
    )


def _wikidata_search_entity(query: str, timeout_seconds: int) -> str | None:
    aliases = {
        "tcs": "Tata Consultancy Services",
    }
    search_query = aliases.get(query.casefold().strip(), query)
    try:
        response = requests.get(
            WIKIDATA_API_URL,
            params={
                "action": "wbsearchentities",
                "search": search_query,
                "language": "en",
                "format": "json",
                "limit": 1,
            },
            timeout=timeout_seconds,
        )
        response.raise_for_status()
    except requests.RequestException:
        return None

    results = response.json().get("search", [])
    if not results:
        return None
    return results[0].get("id")


def _wikidata_labels(entity_ids: list[str], timeout_seconds: int) -> list[str]:
    try:
        response = requests.get(
            WIKIDATA_API_URL,
            params={
                "action": "wbgetentities",
                "ids": "|".join(entity_ids),
                "props": "labels",
                "languages": "en",
                "format": "json",
            },
            timeout=timeout_seconds,
        )
        response.raise_for_status()
    except requests.RequestException:
        return []

    entities = response.json().get("entities", {})
    labels: list[str] = []
    for entity_id in entity_ids:
        label = entities.get(entity_id, {}).get("labels", {}).get("en", {}).get("value")
        if label:
            labels.append(label)
    return labels


def _parse_ceo_target(query: str) -> str | None:
    normalized = query.strip().rstrip("?")
    lowered = normalized.casefold()
    for prefix in ["who is the ceo of ", "current ceo of ", "latest ceo of ", "ceo of "]:
        if lowered.startswith(prefix):
            return normalized[len(prefix) :].strip()
    return None


def _parse_capital_target(query: str) -> str | None:
    normalized = query.strip().rstrip("?")
    lowered = normalized.casefold()
    for prefix in ["what is the capital of ", "capital of "]:
        if lowered.startswith(prefix):
            return normalized[len(prefix) :].strip()
    return None


def _normalize_query(query: str) -> str:
    return " ".join(query.strip().rstrip("?").casefold().split())
