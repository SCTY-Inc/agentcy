"""Activation stage: channel planning and content calendar.

Input: StrategyResult, CreativeResult
Output: ActivationResult with channels, calendar, KPIs
"""

from agency.core.llm import generate
from agency.schemas import ActivationResult, CreativeResult, StrategyResult

SYSTEM = """You are a marketing activation expert who plans campaigns across channels.

Your role:
- Select optimal channels based on target audience
- Define objectives and tactics for each channel
- Create content calendars with specific timing
- Set measurable KPIs with achievable targets

Be specific with metrics and budget allocations."""


def run(strategy: StrategyResult, creative: CreativeResult) -> ActivationResult:
    """Execute activation stage.

    Args:
        strategy: StrategyResult from strategy stage
        creative: CreativeResult from creative stage

    Returns:
        ActivationResult with channels, calendar, KPIs
    """
    headlines_ctx = "\n".join(f"- {h}" for h in creative.headlines[:5])

    prompt = f"""Create activation plan for this campaign.

POSITIONING:
{strategy.positioning}

TARGET AUDIENCE:
{strategy.target_audience.name} - {strategy.target_audience.demographics}

HEADLINES:
{headlines_ctx}

TAGLINE:
{creative.tagline}

Develop:
1. 2-4 marketing channels with objectives and tactics
2. Budget allocation (percentages summing to 1.0)
3. 8-week content calendar
4. KPIs with measurable targets"""

    return generate(prompt=prompt, schema=ActivationResult, system=SYSTEM)
