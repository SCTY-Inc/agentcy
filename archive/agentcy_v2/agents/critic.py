"""Critic agent for quality review and brand validation.

Reviews artifacts against quality rubrics and brand guidelines.
Provides scores and improvement recommendations.
"""

from pydantic import BaseModel, Field

from agentcy.llm import generate
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


CRITIC_SYSTEM = """You are a senior creative director who reviews campaign artifacts for quality.

Your role is to:
- Review artifacts against quality rubrics
- Score each rubric item and calculate overall score
- Identify specific strengths to preserve
- Provide actionable improvement recommendations
- Check brand voice alignment
- Be constructive but rigorous

Set approved=True only if overall_score >= 0.7."""


RUBRICS = {
    "research": """
RESEARCH RUBRIC:
- sources: 5+ credible sources cited
- insights: 3+ actionable insights extracted
- competitors: Competitor analysis included
- assumptions: Assumptions clearly stated
- claims: No unsubstantiated claims
""",
    "strategy": """
STRATEGY RUBRIC:
- positioning: Clear positioning statement
- audience: Target audience persona defined
- pillars: 3+ messaging pillars identified
- proofs: Proof points for each pillar
- risks: Risks and mitigation noted
""",
    "copy": """
COPY RUBRIC:
- headlines: 3+ headline variants
- voice: Body copy matches brand voice
- cta: Clear CTA in each variant
- compliance: No brand voice violations
- format: Scannable format
""",
    "activation": """
ACTIVATION RUBRIC:
- channels: 2+ channels defined
- budget: Budget allocation specified
- calendar: Content calendar with dates
- kpis: KPIs with targets
- measurement: Measurement approach clear
""",
}


def review_artifact(
    artifact_content: str,
    artifact_type: str,
    brand: BrandKit | None = None,
    model_id: str = "gemini-3-flash-preview",
    **kwargs,  # Accept extra args for backwards compat
) -> QualityReview:
    """Review an artifact for quality.

    Args:
        artifact_content: Content of the artifact to review
        artifact_type: Type of artifact (research, strategy, copy, activation)
        brand: Brand kit for alignment checking
        model_id: Gemini model to use

    Returns:
        QualityReview with scores and feedback
    """
    # Build brand context
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

    rubric = RUBRICS.get(artifact_type, "Apply general quality standards.")

    prompt = f"""Review this {artifact_type} artifact for quality.

ARTIFACT:
{artifact_content}

{rubric}
{brand_context}

Provide a comprehensive quality review:
1. Score each rubric item (0.0-1.0)
2. Calculate overall score (average of rubric scores)
3. List specific strengths to preserve
4. List actionable improvements
5. Score brand alignment (0.0-1.0)
6. Set approved=True only if overall_score >= 0.7

Set artifact_type to: {artifact_type}"""

    try:
        result = generate(
            prompt=prompt,
            model=model_id,
            schema=QualityReview,
            system=CRITIC_SYSTEM,
            thinking="low",
        )
        return result
    except Exception as e:
        return QualityReview(
            artifact_type=artifact_type,
            overall_score=0.0,
            strengths=[],
            improvements=[f"Review failed: {e}"],
            brand_alignment_score=0.0,
            rubric_scores={},
            approved=False,
            notes="Manual review required",
        )
