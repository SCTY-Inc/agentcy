"""Copywriter agent with brand voice constraints.

Generates headlines, body copy, and CTAs that match brand guidelines.
Returns structured CopyDeck artifacts.
"""

from agno.agent import Agent
from agno.models.anthropic import Claude

from agentcy.models.artifacts import CopyDeck
from agentcy.models.brand import BrandKit


def create_copywriter(
    campaign_id: str,
    brand: BrandKit | None = None,
    model_id: str = "claude-sonnet-4-20250514",
    debug: bool = False,
) -> Agent:
    """Create a Copywriter agent.

    Args:
        campaign_id: ID of the current campaign
        brand: Brand kit for voice guidelines
        model_id: Anthropic model to use
        debug: Enable debug logging

    Returns:
        Configured Agno Agent
    """
    brand_instructions = []
    if brand:
        if brand.voice.tone:
            brand_instructions.append(f"Write in a {', '.join(brand.voice.tone)} tone.")
        if brand.voice.avoid:
            brand_instructions.append(
                f"NEVER use these words/styles: {', '.join(brand.voice.avoid)}"
            )
        if brand.tagline:
            brand_instructions.append(f"Align with brand tagline: '{brand.tagline}'")

    return Agent(
        name="Copywriter",
        model=Claude(id=model_id),
        output_schema=CopyDeck,
        description="You are an expert copywriter who creates compelling marketing copy.",
        instructions=[
            "Generate 3+ headline variants that grab attention.",
            "Write 2+ body copy variants that build interest and desire.",
            "Create 2+ CTA variants that drive action.",
            "Apply AIDA framework: Attention, Interest, Desire, Action.",
            "Keep headlines under 10 words for impact.",
            "Use active voice and benefit-focused language.",
            "Score your own copy against brand voice guidelines (0.0-1.0).",
            *brand_instructions,
            f"Always set campaign_id to '{campaign_id}' in your response.",
        ],
        add_datetime_to_context=True,
        debug_mode=debug,
    )


def run_copywriting(
    strategy_brief: str,
    campaign_id: str,
    brand: BrandKit | None = None,
    model_id: str = "claude-sonnet-4-20250514",
) -> CopyDeck:
    """Generate copy based on strategy.

    Args:
        strategy_brief: Strategy brief summary
        campaign_id: ID of the current campaign
        brand: Brand kit for voice guidelines
        model_id: Anthropic model to use

    Returns:
        Structured CopyDeck
    """
    agent = create_copywriter(
        campaign_id=campaign_id, brand=brand, model_id=model_id
    )
    result = agent.run(
        f"""Create a copy deck based on this strategy brief.

STRATEGY:
{strategy_brief}

Generate headlines, body copy, and CTAs that align with the messaging pillars."""
    )

    if hasattr(result, "content") and isinstance(result.content, CopyDeck):
        return result.content

    return CopyDeck(
        campaign_id=campaign_id,
        headline_variants=["Copy generation requires manual review"],
        body_variants=[],
        cta_variants=[],
        brand_voice_score=0.0,
    )
