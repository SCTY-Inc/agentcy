"""Research agent with web search and analysis.

Conducts market research, competitor analysis, and trend identification.
Returns structured ResearchReport artifacts.
"""

from agentcy.llm import generate
from agentcy.models.artifacts import ResearchReport
from agentcy.tools.research import search_web

RESEARCH_SYSTEM = """You are a market research expert. Your role is to:
- Conduct thorough research on the given topic or brief
- Analyze competitor positioning and strategies
- Extract actionable insights from your findings
- Identify assumptions that need validation

Always provide specific, evidence-based insights. Be thorough but concise."""


def run_research(
    brief: str,
    campaign_id: str,
    model_id: str = "gemini-3-flash-preview",
    **kwargs,  # Accept extra args for backwards compat
) -> ResearchReport:
    """Run research for a campaign brief.

    Args:
        brief: Campaign brief text
        campaign_id: ID of the current campaign
        model_id: Gemini model to use

    Returns:
        Structured ResearchReport
    """
    # Gather research data via tools
    search_results = search_web(brief, num_results=5)

    # Format search results for context
    sources_context = "\n".join(
        f"- {r['title']}: {r['snippet']} ({r['url']})"
        for r in search_results
    )

    prompt = f"""Research the following campaign brief and provide a comprehensive report.

BRIEF:
{brief}

SEARCH RESULTS:
{sources_context}

Analyze these sources and provide:
1. Key insights relevant to the campaign
2. Competitor analysis (if applicable)
3. Assumptions that need validation

Set campaign_id to: {campaign_id}

Return a structured research report."""

    try:
        result = generate(
            prompt=prompt,
            model=model_id,
            schema=ResearchReport,
            system=RESEARCH_SYSTEM,
            thinking="low",
        )
        return result
    except Exception as e:
        # Fallback on parsing failure
        return ResearchReport(
            campaign_id=campaign_id,
            sources=[],
            insights=[f"Research completed but parsing failed: {e}"],
            competitors=[],
            assumptions=["Manual review recommended"],
        )
