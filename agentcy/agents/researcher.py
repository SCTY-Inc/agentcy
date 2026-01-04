"""Research agent with web search and analysis tools.

Conducts market research, competitor analysis, and trend identification.
Returns structured ResearchReport artifacts.

Uses Agno Culture for shared marketing frameworks and quality standards.
"""

from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.google import Gemini

from agentcy.models.artifacts import CompetitorAnalysis, ResearchReport, Source


def create_researcher(
    campaign_id: str,
    model_id: str = "gemini-2.5-flash-lite",
    db: SqliteDb | None = None,
    debug: bool = False,
) -> Agent:
    """Create a Researcher agent.

    Args:
        campaign_id: ID of the current campaign
        model_id: Gemini model to use
        db: Agno database for Culture access
        debug: Enable debug logging

    Returns:
        Configured Agno Agent with Culture context
    """
    from agentcy.tools.research import search_web, scrape_url

    return Agent(
        name="Researcher",
        model=Gemini(id=model_id),
        tools=[search_web, scrape_url],
        output_schema=ResearchReport,
        description="You are a market research expert.",
        instructions=[
            "Conduct thorough research on the given topic or brief.",
            "Search for relevant sources using the search_web tool.",
            "Analyze competitor positioning and strategies.",
            "Extract actionable insights from your findings.",
            "Cite all sources with URLs.",
            "Identify assumptions that need validation.",
            f"Always set campaign_id to '{campaign_id}' in your response.",
        ],
        # Culture integration
        db=db,
        add_culture_to_context=True if db else False,
        update_cultural_knowledge=False,  # Research doesn't update culture
        add_datetime_to_context=True,
        debug_mode=debug,
    )


def run_research(
    brief: str,
    campaign_id: str,
    model_id: str = "gemini-2.5-flash-lite",
    db: SqliteDb | None = None,
) -> ResearchReport:
    """Run research for a campaign brief.

    Args:
        brief: Campaign brief text
        campaign_id: ID of the current campaign
        model_id: Gemini model to use
        db: Agno database for Culture access

    Returns:
        Structured ResearchReport
    """
    agent = create_researcher(campaign_id=campaign_id, model_id=model_id, db=db)
    result = agent.run(
        f"Research the following brief and provide a comprehensive report:\n\n{brief}"
    )

    # Parse structured output
    if hasattr(result, "content") and isinstance(result.content, ResearchReport):
        return result.content

    # Fallback: create minimal report if parsing fails
    return ResearchReport(
        campaign_id=campaign_id,
        sources=[],
        insights=["Research completed but structured parsing failed"],
        competitors=[],
        assumptions=["Manual review recommended"],
    )
