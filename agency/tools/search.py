"""Search backends: Serper, Exa, or stub.

Configurable via environment:
- AGENCY_LIVE_TOOLS=1 to enable live search
- AGENCY_SEARCH_BACKEND=serper|exa (default: serper)
"""

import os
from dataclasses import dataclass


@dataclass
class SearchResult:
    """Unified search result."""

    url: str
    title: str
    snippet: str


def search(query: str, num_results: int = 5) -> list[SearchResult]:
    """Search web using configured backend.

    Args:
        query: Search query
        num_results: Number of results to return

    Returns:
        List of SearchResult
    """
    if os.getenv("AGENCY_LIVE_TOOLS", "").lower() not in ("1", "true"):
        return _stub_search(query, num_results)

    backend = os.getenv("AGENCY_SEARCH_BACKEND", "serper").lower()

    if backend == "exa":
        return _exa_search(query, num_results)
    return _serper_search(query, num_results)


def _stub_search(query: str, num_results: int) -> list[SearchResult]:
    """Stub search for development without API keys."""
    return [
        SearchResult(
            url=f"https://example.com/result-{i + 1}",
            title=f"Result {i + 1} for: {query[:50]}",
            snippet="Stub result. Set AGENCY_LIVE_TOOLS=1 for real search.",
        )
        for i in range(min(num_results, 3))
    ]


def _serper_search(query: str, num_results: int) -> list[SearchResult]:
    """Search via Serper API (Google Search).

    Docs: https://serper.dev/
    Pricing: $50/mo for 50k searches
    """
    import httpx

    api_key = os.getenv("SERPER_API_KEY")
    if not api_key:
        raise ValueError("SERPER_API_KEY required. Get one at https://serper.dev/")

    try:
        response = httpx.post(
            "https://google.serper.dev/search",
            headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
            json={"q": query, "num": num_results},
            timeout=30.0,
        )
        response.raise_for_status()

        results = []
        for item in response.json().get("organic", [])[:num_results]:
            results.append(
                SearchResult(
                    url=item.get("link", ""),
                    title=item.get("title", ""),
                    snippet=item.get("snippet", ""),
                )
            )
        return results

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            raise ValueError("Invalid SERPER_API_KEY")
        if e.response.status_code == 429:
            raise ValueError("Serper rate limit exceeded")
        raise ValueError(f"Serper API error: {e.response.status_code}")
    except httpx.TimeoutException:
        raise ValueError("Serper API timeout")


def _exa_search(query: str, num_results: int) -> list[SearchResult]:
    """Search via Exa API (neural/semantic search).

    Docs: https://docs.exa.ai/
    Pricing: Pay-per-use, ~$0.01/search
    """
    import httpx

    api_key = os.getenv("EXA_API_KEY")
    if not api_key:
        raise ValueError("EXA_API_KEY required. Get one at https://exa.ai/")

    try:
        response = httpx.post(
            "https://api.exa.ai/search",
            headers={
                "x-api-key": api_key,
                "Content-Type": "application/json",
            },
            json={
                "query": query,
                "numResults": num_results,
                "useAutoprompt": True,
                "type": "neural",
            },
            timeout=30.0,
        )
        response.raise_for_status()

        results = []
        for item in response.json().get("results", [])[:num_results]:
            results.append(
                SearchResult(
                    url=item.get("url", ""),
                    title=item.get("title", ""),
                    snippet=item.get("text", "")[:300] if item.get("text") else "",
                )
            )
        return results

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            raise ValueError("Invalid EXA_API_KEY")
        if e.response.status_code == 429:
            raise ValueError("Exa rate limit exceeded")
        raise ValueError(f"Exa API error: {e.response.status_code}")
    except httpx.TimeoutException:
        raise ValueError("Exa API timeout")
