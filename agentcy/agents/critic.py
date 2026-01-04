"""Critic agent for quality review and brand validation.

Reviews artifacts against quality rubrics and brand guidelines.
Provides scores and improvement recommendations.
"""

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from pydantic import BaseModel, Field

from agentcy.models.brand import BrandKit


class QualityReview(BaseModel):
    """Quality review result for an artifact."""

    artifact_type: str = Field(description="Type of artifact reviewed")
    overall_score: float = Field(ge=0.0, le=1.0, description="Overall quality score")
    strengths: list[str] = Field(default_factory=list)
    improvements: list[str] = Field(default_factory=list)
    brand_alignment_score: float = Field(
        ge=0.0, le=1.0, description="How well it aligns with brand voice"
    )
    rubric_scores: dict[str, float] = Field(
        default_factory=dict,
        description="Individual rubric item scores",
    )
    approved: bool = Field(
        default=False, description="Whether artifact meets quality threshold"
    )
    notes: str = Field(default="", description="Additional reviewer notes")


def create_critic(
    brand: BrandKit | None = None,
    model_id: str = "gpt-4o",
    debug: bool = False,
) -> Agent:
    """Create a Critic agent.

    Args:
        brand: Brand kit for alignment checking
        model_id: OpenAI model to use
        debug: Enable debug logging

    Returns:
        Configured Agno Agent
    """
    brand_context = ""
    if brand:
        tone = ", ".join(brand.voice.tone) if brand.voice.tone else "professional"
        avoid = ", ".join(brand.voice.avoid) if brand.voice.avoid else "none specified"
        brand_context = f"""
BRAND GUIDELINES:
- Brand: {brand.name}
- Tone: {tone}
- Avoid: {avoid}
- Tagline: {brand.tagline or 'Not specified'}
"""

    return Agent(
        name="Critic",
        model=OpenAIChat(id=model_id),
        output_schema=QualityReview,
        description="You are a senior creative director who reviews campaign artifacts for quality.",
        instructions=[
            "Review artifacts against the quality rubrics.",
            "Score each rubric item and calculate overall score.",
            "Identify specific strengths to preserve.",
            "Provide actionable improvement recommendations.",
            "Check brand voice alignment if guidelines provided.",
            "Set approved=True only if overall_score >= 0.7.",
            "Be constructive but rigorous in your feedback.",
            brand_context,
        ],
        add_datetime_to_context=True,
        debug_mode=debug,
    )


def review_artifact(
    artifact_content: str,
    artifact_type: str,
    brand: BrandKit | None = None,
    model_id: str = "gpt-4o",
) -> QualityReview:
    """Review an artifact for quality.

    Args:
        artifact_content: Content of the artifact to review
        artifact_type: Type of artifact (research, strategy, copy, activation)
        brand: Brand kit for alignment checking
        model_id: OpenAI model to use

    Returns:
        QualityReview with scores and feedback
    """
    agent = create_critic(brand=brand, model_id=model_id)

    rubric_context = _get_rubric_for_type(artifact_type)

    result = agent.run(
        f"""Review this {artifact_type} artifact for quality.

ARTIFACT:
{artifact_content}

{rubric_context}

Provide a comprehensive quality review with scores and recommendations."""
    )

    if hasattr(result, "content") and isinstance(result.content, QualityReview):
        return result.content

    return QualityReview(
        artifact_type=artifact_type,
        overall_score=0.0,
        strengths=[],
        improvements=["Quality review requires manual assessment"],
        brand_alignment_score=0.0,
        rubric_scores={},
        approved=False,
        notes="Structured parsing failed",
    )


def _get_rubric_for_type(artifact_type: str) -> str:
    """Get the quality rubric for an artifact type."""
    rubrics = {
        "research": """
RESEARCH RUBRIC:
- [ ] 5+ credible sources cited
- [ ] 3+ actionable insights extracted
- [ ] Competitor analysis included
- [ ] Assumptions clearly stated
- [ ] No unsubstantiated claims
""",
        "strategy": """
STRATEGY RUBRIC:
- [ ] Clear positioning statement
- [ ] Target audience persona defined
- [ ] 3+ messaging pillars identified
- [ ] Proof points for each pillar
- [ ] Risks and mitigation noted
""",
        "copy": """
COPY RUBRIC:
- [ ] 3+ headline variants
- [ ] Body copy matches brand voice
- [ ] Clear CTA in each variant
- [ ] No brand voice violations
- [ ] Scannable format
""",
        "activation": """
ACTIVATION RUBRIC:
- [ ] 2+ channels defined
- [ ] Budget allocation specified
- [ ] Content calendar with dates
- [ ] KPIs with targets
- [ ] Measurement approach clear
""",
    }
    return rubrics.get(artifact_type, "Apply general quality standards.")
