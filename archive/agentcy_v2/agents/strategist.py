"""Strategy agent with marketing frameworks.

Develops positioning, messaging pillars, and target audience personas.
Returns structured StrategyBrief artifacts.
"""

from agentcy.llm import generate
from agentcy.models.artifacts import AudiencePersona, StrategyBrief

STRATEGY_SYSTEM = """You are a marketing strategist with deep expertise in positioning and messaging.

Your role is to:
- Develop clear positioning statements that differentiate from competitors
- Define detailed target audience personas
- Create messaging pillars that support the positioning
- Apply marketing frameworks (STP, 4Ps, AIDA) as appropriate

Be specific and actionable in your recommendations."""


def run_strategy(
    research_summary: str,
    brief: str,
    campaign_id: str,
    model_id: str = "gemini-3-flash-preview",
    **kwargs,  # Accept extra args for backwards compat
) -> StrategyBrief:
    """Develop strategy based on research.

    Args:
        research_summary: Summary of research findings
        brief: Original campaign brief
        campaign_id: ID of the current campaign
        model_id: Gemini model to use

    Returns:
        Structured StrategyBrief
    """
    prompt = f"""Develop a comprehensive marketing strategy based on this research and brief.

BRIEF:
{brief}

RESEARCH FINDINGS:
{research_summary}

Create a strategy brief with:
1. Clear positioning statement that differentiates from competitors
2. Detailed target audience persona (name, demographics, pain points, motivations)
3. 3-5 messaging pillars that support the positioning
4. Proof points for each messaging pillar
5. Potential risks and objections

Set campaign_id to: {campaign_id}"""

    try:
        result = generate(
            prompt=prompt,
            model=model_id,
            schema=StrategyBrief,
            system=STRATEGY_SYSTEM,
            thinking="low",
        )
        return result
    except Exception as e:
        return StrategyBrief(
            campaign_id=campaign_id,
            positioning=f"Strategy generation failed: {e}",
            target_audience=AudiencePersona(
                name="To be defined",
                demographics="",
                pain_points=[],
                motivations=[],
            ),
            messaging_pillars=[],
            proof_points=[],
            risks=["Manual review required"],
        )
