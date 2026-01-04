"""Strategy agent with marketing frameworks.

Develops positioning, messaging pillars, and target audience personas.
Returns structured StrategyBrief artifacts.

Uses Agno Culture for shared marketing frameworks (STP, 4Ps, AIDA, etc.).
"""

from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.google import Gemini

from agentcy.models.artifacts import StrategyBrief


def create_strategist(
    campaign_id: str,
    model_id: str = "gemini-3-flash-preview",
    db: SqliteDb | None = None,
    debug: bool = False,
) -> Agent:
    """Create a Strategist agent.

    Args:
        campaign_id: ID of the current campaign
        model_id: Gemini model to use
        db: Agno database for Culture access
        debug: Enable debug logging

    Returns:
        Configured Agno Agent with Culture context
    """
    return Agent(
        name="Strategist",
        model=Gemini(id=model_id),
        output_schema=StrategyBrief,
        description="You are a marketing strategist with deep expertise in positioning and messaging.",
        instructions=[
            "Develop a clear positioning statement that differentiates from competitors.",
            "Define a detailed target audience persona with demographics, pain points, and motivations.",
            "Create 3-5 messaging pillars that support the positioning.",
            "Provide proof points for each messaging pillar.",
            "Identify risks and potential objections.",
            "Apply frameworks from Culture (STP, 4Ps, AIDA) as appropriate.",
            f"Always set campaign_id to '{campaign_id}' in your response.",
        ],
        # Culture integration
        db=db,
        add_culture_to_context=True if db else False,
        update_cultural_knowledge=False,  # Strategy uses but doesn't update culture
        add_datetime_to_context=True,
        debug_mode=debug,
    )


def run_strategy(
    research_summary: str,
    brief: str,
    campaign_id: str,
    model_id: str = "gemini-3-flash-preview",
    db: SqliteDb | None = None,
) -> StrategyBrief:
    """Develop strategy based on research.

    Args:
        research_summary: Summary of research findings
        brief: Original campaign brief
        campaign_id: ID of the current campaign
        model_id: Gemini model to use
        db: Agno database for Culture access

    Returns:
        Structured StrategyBrief
    """
    agent = create_strategist(campaign_id=campaign_id, model_id=model_id, db=db)
    result = agent.run(
        f"""Develop a comprehensive marketing strategy based on this research and brief.

BRIEF:
{brief}

RESEARCH FINDINGS:
{research_summary}

Create a strategy brief with positioning, target audience, and messaging pillars."""
    )

    if hasattr(result, "content") and isinstance(result.content, StrategyBrief):
        return result.content

    from agentcy.models.artifacts import AudiencePersona

    return StrategyBrief(
        campaign_id=campaign_id,
        positioning="Strategy generation requires manual review",
        target_audience=AudiencePersona(
            name="To be defined",
            demographics="",
            pain_points=[],
            motivations=[],
        ),
        messaging_pillars=[],
        proof_points=[],
        risks=["Structured parsing failed - manual review needed"],
    )
