"""Research stage: market research and competitor analysis.

Input: Campaign brief (str)
Output: ResearchResult with insights, competitors, sources
"""

import os

from pydantic import BaseModel, Field

from agency.core.llm import generate


class Source(BaseModel):
    """Research source reference."""

    url: str
    title: str
    snippet: str = ""


class Competitor(BaseModel):
    """Competitor analysis."""

    name: str
    positioning: str
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)


class ResearchResult(BaseModel):
    """Output of research stage."""

    brief: str
    insights: list[str] = Field(default_factory=list)
    competitors: list[Competitor] = Field(default_factory=list)
    sources: list[Source] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)


SYSTEM = """You are a market research expert. Analyze the campaign brief and provide:
- Key market insights relevant to the campaign
- Competitor positioning and analysis
- Assumptions that need validation

Be specific and evidence-based. Focus on actionable intelligence."""


def _search_web(query: str, num_results: int = 5) -> list[dict]:
    """Search web for research (stub unless AGENCY_LIVE_TOOLS=1)."""
    if os.getenv("AGENCY_LIVE_TOOLS", "").lower() in ("1", "true"):
        return _live_search(query, num_results)
    return [
        {
            "title": f"Result {i + 1} for: {query}",
            "url": f"https://example.com/{i + 1}",
            "snippet": f"Stub result for {query}",
        }
        for i in range(min(num_results, 3))
    ]


def _live_search(query: str, num_results: int) -> list[dict]:
    """Live web search via Serper API."""
    import httpx

    api_key = os.getenv("SERPER_API_KEY")
    if not api_key:
        raise ValueError("SERPER_API_KEY required for live search")
    response = httpx.post(
        "https://google.serper.dev/search",
        headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
        json={"q": query, "num": num_results},
        timeout=30.0,
    )
    response.raise_for_status()
    return [
        {"title": r.get("title", ""), "url": r.get("link", ""), "snippet": r.get("snippet", "")}
        for r in response.json().get("organic", [])[:num_results]
    ]


def run(brief: str) -> ResearchResult:
    """Execute research stage.

    Args:
        brief: Campaign brief text

    Returns:
        ResearchResult with insights, competitors, sources
    """
    search_results = _search_web(brief, num_results=5)
    sources_ctx = "\n".join(f"- {r['title']}: {r['snippet']} ({r['url']})" for r in search_results)

    prompt = f"""Research the following campaign brief.

BRIEF:
{brief}

SEARCH RESULTS:
{sources_ctx}

Analyze and provide:
1. Key insights relevant to the campaign
2. Competitor analysis (if applicable)
3. Assumptions that need validation

Set brief to the original brief text."""

    return generate(prompt=prompt, schema=ResearchResult, system=SYSTEM)
