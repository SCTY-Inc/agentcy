"""Visual agent with image generation tools.

Creates visual concepts and generates images using Replicate.
"""

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from pydantic import BaseModel, Field


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


def create_visual_agent(
    campaign_id: str,
    model_id: str = "gpt-4o",
    debug: bool = False,
) -> Agent:
    """Create a Visual agent.

    Args:
        campaign_id: ID of the current campaign
        model_id: OpenAI model to use
        debug: Enable debug logging

    Returns:
        Configured Agno Agent
    """
    from agentcy.tools.visual import generate_image

    return Agent(
        name="Visual Director",
        model=OpenAIChat(id=model_id),
        tools=[generate_image],
        output_schema=VisualConcept,
        description="You are a visual director who creates compelling campaign imagery.",
        instructions=[
            "Develop a cohesive visual concept that supports the campaign message.",
            "Define a consistent style and color palette.",
            "Create detailed image prompts that are specific and actionable.",
            "Generate 2-3 hero images using the generate_image tool.",
            "Ensure visuals align with brand guidelines if provided.",
            f"Always set campaign_id to '{campaign_id}' in your response.",
        ],
        add_datetime_to_context=True,
        debug_mode=debug,
    )


def run_visual_creation(
    strategy_brief: str,
    campaign_id: str,
    brand_colors: list[str] | None = None,
    model_id: str = "gpt-4o",
) -> VisualConcept:
    """Create visual concepts and generate images.

    Args:
        strategy_brief: Strategy brief summary
        campaign_id: ID of the current campaign
        brand_colors: Optional brand color palette
        model_id: OpenAI model to use

    Returns:
        VisualConcept with generated images
    """
    agent = create_visual_agent(campaign_id=campaign_id, model_id=model_id)

    color_context = ""
    if brand_colors:
        color_context = f"\n\nBrand colors to incorporate: {', '.join(brand_colors)}"

    result = agent.run(
        f"""Create a visual concept for this campaign.

STRATEGY:
{strategy_brief}
{color_context}

Develop the visual direction and generate hero images."""
    )

    if hasattr(result, "content") and isinstance(result.content, VisualConcept):
        return result.content

    return VisualConcept(
        campaign_id=campaign_id,
        concept_name="Visual concept requires manual review",
        description="",
        style="",
        color_palette=brand_colors or [],
        image_prompts=[],
        generated_images=[],
    )
