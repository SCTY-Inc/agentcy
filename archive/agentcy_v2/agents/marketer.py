"""Marketer agent for channel planning and activation.

Develops channel strategies, content calendars, and KPIs.
Returns structured ActivationPlan artifacts.
"""

from agentcy.llm import generate
from agentcy.models.artifacts import ActivationPlan

MARKETER_SYSTEM = """You are a marketing activation expert who plans campaigns across channels.

Your role is to:
- Select optimal marketing channels based on target audience
- Define clear objectives and tactics for each channel
- Create realistic content calendars with specific dates
- Set measurable KPIs with achievable targets
- Apply marketing frameworks (funnel stages, 4Ps)

Be specific with dates, metrics, and budget allocations."""


def run_activation_planning(
    strategy_brief: str,
    copy_summary: str,
    campaign_id: str,
    budget_usd: float | None = None,
    model_id: str = "gemini-3-flash-preview",
    **kwargs,  # Accept extra args for backwards compat
) -> ActivationPlan:
    """Create activation plan based on strategy and copy.

    Args:
        strategy_brief: Strategy brief summary
        copy_summary: Summary of copy deck
        campaign_id: ID of the current campaign
        budget_usd: Optional campaign budget in USD
        model_id: Gemini model to use

    Returns:
        Structured ActivationPlan
    """
    budget_context = ""
    if budget_usd:
        budget_context = f"\n\nTotal campaign budget: ${budget_usd:,.0f}"

    prompt = f"""Create an activation plan for this campaign.

STRATEGY:
{strategy_brief}

COPY:
{copy_summary}
{budget_context}

Develop:
1. 2-4 marketing channels with clear objectives and tactics
2. Budget allocation percentages across channels
3. Content calendar with specific dates and content types
4. KPIs with measurable targets for each channel

Set campaign_id to: {campaign_id}"""

    try:
        result = generate(
            prompt=prompt,
            model=model_id,
            schema=ActivationPlan,
            system=MARKETER_SYSTEM,
            thinking="low",
        )
        return result
    except Exception:
        return ActivationPlan(
            campaign_id=campaign_id,
            channels=[],
            content_calendar=[],
            budget_allocation={},
            kpis=[],
        )
