"""Creative stage: copy and headline generation.

Input: StrategyResult
Output: CreativeResult with headlines, body copy, CTAs
"""

from agency.core.llm import generate
from agency.schemas import CreativeResult, StrategyResult

SYSTEM = """You are an expert copywriter creating compelling marketing copy.

Your role:
- Generate attention-grabbing headlines (under 10 words)
- Write body copy that builds interest and desire
- Create clear calls-to-action that drive conversions
- Apply AIDA framework (Attention, Interest, Desire, Action)

Use active voice and benefit-focused language."""


def run(strategy: StrategyResult) -> CreativeResult:
    """Execute creative stage.

    Args:
        strategy: StrategyResult from strategy stage

    Returns:
        CreativeResult with headlines, body copy, CTAs
    """
    pillars_ctx = "\n".join(f"- {p}" for p in strategy.messaging_pillars)

    prompt = f"""Create copy based on this strategy.

POSITIONING:
{strategy.positioning}

TARGET AUDIENCE:
{strategy.target_audience.name} - {strategy.target_audience.demographics}
Pain points: {", ".join(strategy.target_audience.pain_points[:3])}

MESSAGING PILLARS:
{pillars_ctx}

Generate:
1. 5+ headline variants (under 10 words each)
2. 3+ body copy variants (2-3 sentences each)
3. 3+ CTA variants
4. One memorable tagline"""

    return generate(prompt=prompt, schema=CreativeResult, system=SYSTEM)
