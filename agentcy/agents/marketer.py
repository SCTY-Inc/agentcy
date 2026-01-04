"""Marketer agent for channel planning and activation.

Develops channel strategies, content calendars, and KPIs.
Returns structured ActivationPlan artifacts.

Uses Agno Culture for marketing frameworks and quality standards.
"""

from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.google import Gemini

from agentcy.models.artifacts import ActivationPlan


def create_marketer(
    campaign_id: str,
    model_id: str = "gemini-3-flash-preview",
    db: SqliteDb | None = None,
    debug: bool = False,
) -> Agent:
    """Create a Marketer agent.

    Args:
        campaign_id: ID of the current campaign
        model_id: Gemini model to use
        db: Agno database for Culture access
        debug: Enable debug logging

    Returns:
        Configured Agno Agent with Culture context
    """
    return Agent(
        name="Marketer",
        model=Gemini(id=model_id),
        output_schema=ActivationPlan,
        description="You are a marketing activation expert who plans campaigns across channels.",
        instructions=[
            "Select 2-4 marketing channels based on target audience.",
            "Define clear objectives and tactics for each channel.",
            "Allocate budget percentages across channels.",
            "Create a content calendar with specific dates and content types.",
            "Define measurable KPIs with targets for each channel.",
            "Apply marketing frameworks from Culture (4Ps, funnel stages).",
            f"Always set campaign_id to '{campaign_id}' in your response.",
        ],
        # Culture integration
        db=db,
        add_culture_to_context=True if db else False,
        update_cultural_knowledge=False,
        add_datetime_to_context=True,
        debug_mode=debug,
    )


def run_activation_planning(
    strategy_brief: str,
    copy_summary: str,
    campaign_id: str,
    budget_usd: float | None = None,
    model_id: str = "gemini-3-flash-preview",
    db: SqliteDb | None = None,
) -> ActivationPlan:
    """Create activation plan based on strategy and copy.

    Args:
        strategy_brief: Strategy brief summary
        copy_summary: Summary of copy deck
        campaign_id: ID of the current campaign
        budget_usd: Optional campaign budget in USD
        model_id: Gemini model to use
        db: Agno database for Culture access

    Returns:
        Structured ActivationPlan
    """
    agent = create_marketer(campaign_id=campaign_id, model_id=model_id, db=db)

    budget_context = ""
    if budget_usd:
        budget_context = f"\n\nTotal campaign budget: ${budget_usd:,.0f}"

    result = agent.run(
        f"""Create an activation plan for this campaign.

STRATEGY:
{strategy_brief}

COPY:
{copy_summary}
{budget_context}

Plan the channel mix, content calendar, and KPIs."""
    )

    if hasattr(result, "content") and isinstance(result.content, ActivationPlan):
        return result.content

    return ActivationPlan(
        campaign_id=campaign_id,
        channels=[],
        content_calendar=[],
        budget_allocation={},
        kpis=[],
    )
