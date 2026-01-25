"""Visual agent with image generation.

Creates visual concepts and generates images using Replicate.
"""

from pydantic import BaseModel, Field

from agentcy.llm import generate
from agentcy.tools.visual import generate_image


class VisualConcept(BaseModel):
    """Visual concept for campaign imagery."""

    campaign_id: str
    concept_name: str
    description: str = Field(description="Detailed description of the visual concept")
    style: str = Field(description="Visual style (e.g., 'minimalist', 'bold', 'photorealistic')")
    color_palette: list[str] = Field(default_factory=list)
    image_prompts: list[str] = Field(
        default_factory=list,
        description="Detailed prompts for image generation",
    )
    generated_images: list[str] = Field(
        default_factory=list,
        description="URLs or paths to generated images",
    )


VISUAL_SYSTEM = """You are a visual director who creates compelling campaign imagery.

Your role is to:
- Develop cohesive visual concepts that support campaign messaging
- Define consistent visual styles and color palettes
- Create detailed, specific image prompts
- Ensure visuals align with brand guidelines

Be specific with visual directions - include style, mood, composition, and color details."""


def run_visual_creation(
    strategy_brief: str,
    campaign_id: str,
    brand_colors: list[str] | None = None,
    model_id: str = "gemini-3-flash-preview",
    **kwargs,  # Accept extra args for backwards compat
) -> VisualConcept:
    """Create visual concepts and generate images.

    Args:
        strategy_brief: Strategy brief summary
        campaign_id: ID of the current campaign
        brand_colors: Optional brand color palette
        model_id: Gemini model to use

    Returns:
        VisualConcept with generated images
    """
    color_context = ""
    if brand_colors:
        color_context = f"\n\nBrand colors to incorporate: {', '.join(brand_colors)}"

    prompt = f"""Create a visual concept for this campaign.

STRATEGY:
{strategy_brief}
{color_context}

Develop:
1. A cohesive visual concept name and description
2. Visual style direction
3. Color palette (use brand colors if provided)
4. 2-3 detailed image prompts for hero imagery

Set campaign_id to: {campaign_id}"""

    try:
        result = generate(
            prompt=prompt,
            model=model_id,
            schema=VisualConcept,
            system=VISUAL_SYSTEM,
            thinking="low",
        )

        # Generate images from prompts if any
        if result.image_prompts:
            generated = []
            for img_prompt in result.image_prompts[:3]:  # Limit to 3
                try:
                    url = generate_image(img_prompt)
                    if url:
                        generated.append(url)
                except Exception:
                    pass  # Skip failed generations
            result.generated_images = generated

        return result
    except Exception as e:
        return VisualConcept(
            campaign_id=campaign_id,
            concept_name=f"Visual concept failed: {e}",
            description="",
            style="",
            color_palette=brand_colors or [],
            image_prompts=[],
            generated_images=[],
        )
