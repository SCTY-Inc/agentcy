"""Research stage: market research and competitor analysis.

Input: Campaign brief (str)
Output: ResearchResult with insights, competitors, sources
"""

from agency.core.llm import generate
from agency.schemas import ResearchResult, Source
from agency.tools.search import search

SYSTEM = """You are a market research expert. Analyze the campaign brief and provide:
- Key market insights relevant to the campaign
- Competitor positioning and analysis
- Assumptions that need validation

Be specific and evidence-based. Focus on actionable intelligence."""


def run(brief: str) -> ResearchResult:
    """Execute research stage.

    Args:
        brief: Campaign brief text

    Returns:
        ResearchResult with insights, competitors, sources
    """
    # Search for market context
    search_results = search(brief, num_results=5)

    # Format search results for prompt
    sources_ctx = "\n".join(
        f"- {r.title[:80]}: {r.snippet[:150]} ({r.url})" for r in search_results
    )

    # Convert to schema format for output
    sources = [Source(url=r.url, title=r.title, snippet=r.snippet) for r in search_results]

    prompt = f"""Research the following campaign brief.

BRIEF:
{brief}

SEARCH RESULTS:
{sources_ctx}

Analyze and provide:
1. Key insights relevant to the campaign
2. Competitor analysis (if applicable)
3. Assumptions that need validation

Set brief to the original brief text.
Include the search results as sources."""

    result = generate(prompt=prompt, schema=ResearchResult, system=SYSTEM)

    # Ensure sources are included
    if not result.sources:
        result.sources = sources

    return result
