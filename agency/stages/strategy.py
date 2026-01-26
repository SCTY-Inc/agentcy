"""Strategy stage: positioning and messaging development.

Input: ResearchResult
Output: StrategyResult with positioning, audience, messaging pillars
"""

from agency.core.llm import generate
from agency.schemas import ResearchResult, StrategyResult

SYSTEM = """You are a marketing strategist with expertise in positioning and messaging.

Your role:
- Develop clear positioning that differentiates from competitors
- Define detailed target audience personas
- Create messaging pillars that support the positioning
- Apply frameworks: STP, 4Ps, AIDA

Be specific and actionable."""


def run(research: ResearchResult) -> StrategyResult:
    """Execute strategy stage.

    Args:
        research: ResearchResult from research stage

    Returns:
        StrategyResult with positioning, audience, messaging
    """
    # Format research for context
    insights_ctx = "\n".join(f"- {i}" for i in research.insights[:10])
    competitors_ctx = "\n".join(f"- {c.name}: {c.positioning}" for c in research.competitors[:5])

    prompt = f"""Develop marketing strategy based on research.

BRIEF:
{research.brief}

KEY INSIGHTS:
{insights_ctx}

COMPETITORS:
{competitors_ctx}

Create strategy with:
1. Clear positioning statement
2. Target audience persona (name, demographics, pain points, motivations)
3. 3-5 messaging pillars
4. Proof points for each pillar
5. Potential risks and objections"""

    return generate(prompt=prompt, schema=StrategyResult, system=SYSTEM)
