"""Copywriter agent with brand voice constraints.

Generates headlines, body copy, and CTAs that match brand guidelines.
Returns structured CopyDeck artifacts.
"""

from agentcy.llm import generate
from agentcy.models.artifacts import CopyDeck
from agentcy.models.brand import BrandKit

COPY_SYSTEM = """You are an expert copywriter who creates compelling marketing copy.

Your role is to:
- Generate attention-grabbing headlines (under 10 words)
- Write body copy that builds interest and desire
- Create clear calls-to-action that drive conversions
- Apply the AIDA framework (Attention, Interest, Desire, Action)
- Use active voice and benefit-focused language

Always match the brand voice guidelines provided."""


def run_copywriting(
    strategy_brief: str,
    campaign_id: str,
    brand: BrandKit | None = None,
    model_id: str = "gemini-3-flash-preview",
    **kwargs,  # Accept extra args for backwards compat
) -> CopyDeck:
    """Generate copy based on strategy.

    Args:
        strategy_brief: Strategy brief summary
        campaign_id: ID of the current campaign
        brand: Brand kit for voice guidelines
        model_id: Gemini model to use

    Returns:
        Structured CopyDeck
    """
    # Build brand context
    brand_context = ""
    if brand:
        brand_context = "\nBRAND GUIDELINES:"
        if brand.voice.tone:
            brand_context += f"\n- Tone: {', '.join(brand.voice.tone)}"
        if brand.voice.avoid:
            brand_context += f"\n- NEVER use: {', '.join(brand.voice.avoid)}"
        if brand.tagline:
            brand_context += f"\n- Align with tagline: '{brand.tagline}'"

    prompt = f"""Create a copy deck based on this strategy brief.

STRATEGY:
{strategy_brief}
{brand_context}

Generate:
1. 3+ headline variants that grab attention (under 10 words each)
2. 2+ body copy variants that build interest and desire
3. 2+ CTA variants that drive action
4. Score your copy against brand voice guidelines (0.0-1.0)

Set campaign_id to: {campaign_id}"""

    try:
        result = generate(
            prompt=prompt,
            model=model_id,
            schema=CopyDeck,
            system=COPY_SYSTEM,
            thinking="low",
        )
        return result
    except Exception as e:
        return CopyDeck(
            campaign_id=campaign_id,
            headline_variants=[f"Copy generation failed: {e}"],
            body_variants=[],
            cta_variants=[],
            brand_voice_score=0.0,
        )
