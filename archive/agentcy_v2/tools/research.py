"""Web search and scraping tools for research.

Tools are stubbed by default. Set AGENTCY_LIVE_TOOLS=1 to enable live API calls.
Requires SERPER_API_KEY for live search.
"""

import os
from typing import Any


def _is_live() -> bool:
    """Check if live tools are enabled."""
    return os.getenv("AGENTCY_LIVE_TOOLS", "").lower() in ("1", "true", "yes")


def search_web(query: str, num_results: int = 5) -> list[dict[str, Any]]:
    """Search the web for information.

    Args:
        query: Search query string
        num_results: Number of results to return (default 5)

    Returns:
        List of search results with title, url, and snippet
    """
    if _is_live():
        return _live_search(query, num_results)
    return _stub_search(query, num_results)


def scrape_url(url: str) -> str:
    """Scrape content from a URL.

    Args:
        url: URL to scrape

    Returns:
        Extracted text content from the page
    """
    if _is_live():
        return _live_scrape(url)
    return _stub_scrape(url)


def _stub_search(query: str, num_results: int) -> list[dict[str, Any]]:
    """Return stub search results for testing."""
    return [
        {
            "title": f"Search result {i+1} for: {query}",
            "url": f"https://example.com/result-{i+1}",
            "snippet": f"This is a stub result for testing. Query: {query}",
        }
        for i in range(min(num_results, 3))
    ]


def _stub_scrape(url: str) -> str:
    """Return stub scrape content for testing."""
    return f"""
[STUB CONTENT]
URL: {url}
This is placeholder content for testing purposes.
In production, this would contain the actual page content.
"""


def _live_search(query: str, num_results: int) -> list[dict[str, Any]]:
    """Perform live web search using Serper API."""
    import httpx

    api_key = os.getenv("SERPER_API_KEY")
    if not api_key:
        raise ValueError("SERPER_API_KEY environment variable required for live search")

    response = httpx.post(
        "https://google.serper.dev/search",
        headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
        json={"q": query, "num": num_results},
        timeout=30.0,
    )
    response.raise_for_status()
    data = response.json()

    results = []
    for item in data.get("organic", [])[:num_results]:
        results.append({
            "title": item.get("title", ""),
            "url": item.get("link", ""),
            "snippet": item.get("snippet", ""),
        })
    return results


def _live_scrape(url: str) -> str:
    """Perform live URL scraping."""
    import httpx
    from bs4 import BeautifulSoup

    response = httpx.get(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; Agentcy/2.0)"},
        timeout=30.0,
        follow_redirects=True,
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Remove script and style elements
    for element in soup(["script", "style", "nav", "footer", "header"]):
        element.decompose()

    # Get text content
    text = soup.get_text(separator="\n", strip=True)

    # Truncate to reasonable length
    max_chars = 10000
    if len(text) > max_chars:
        text = text[:max_chars] + "\n\n[Content truncated]"

    return text
