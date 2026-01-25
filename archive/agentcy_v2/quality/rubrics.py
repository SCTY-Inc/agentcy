"""Scoring rubrics per artifact type.

Defines quality criteria and scoring for each campaign artifact.
"""

from dataclasses import dataclass
from enum import Enum


class ArtifactType(str, Enum):
    """Types of campaign artifacts."""

    RESEARCH = "research"
    STRATEGY = "strategy"
    COPY = "copy"
    ACTIVATION = "activation"
    VISUAL = "visual"


@dataclass
class RubricItem:
    """Single rubric criterion."""

    name: str
    description: str
    weight: float  # 0.0 to 1.0, weights should sum to 1.0
    required: bool = False  # If required, failing = 0 overall score


@dataclass
class Rubric:
    """Complete rubric for an artifact type."""

    artifact_type: ArtifactType
    items: list[RubricItem]
    passing_threshold: float = 0.7

    def validate_weights(self) -> bool:
        """Check that weights sum to approximately 1.0."""
        total = sum(item.weight for item in self.items)
        return 0.99 <= total <= 1.01


# Define rubrics for each artifact type

RESEARCH_RUBRIC = Rubric(
    artifact_type=ArtifactType.RESEARCH,
    items=[
        RubricItem(
            name="sources",
            description="5+ credible sources cited with URLs",
            weight=0.25,
            required=True,
        ),
        RubricItem(
            name="insights",
            description="3+ actionable insights extracted",
            weight=0.25,
            required=True,
        ),
        RubricItem(
            name="competitors",
            description="Competitor analysis included",
            weight=0.20,
        ),
        RubricItem(
            name="assumptions",
            description="Assumptions clearly stated",
            weight=0.15,
        ),
        RubricItem(
            name="claims",
            description="No unsubstantiated claims",
            weight=0.15,
        ),
    ],
)


STRATEGY_RUBRIC = Rubric(
    artifact_type=ArtifactType.STRATEGY,
    items=[
        RubricItem(
            name="positioning",
            description="Clear, differentiated positioning statement",
            weight=0.25,
            required=True,
        ),
        RubricItem(
            name="audience",
            description="Target audience persona defined with demographics and motivations",
            weight=0.20,
            required=True,
        ),
        RubricItem(
            name="pillars",
            description="3+ messaging pillars identified",
            weight=0.25,
            required=True,
        ),
        RubricItem(
            name="proof_points",
            description="Proof points supporting each pillar",
            weight=0.15,
        ),
        RubricItem(
            name="risks",
            description="Risks and mitigation strategies noted",
            weight=0.15,
        ),
    ],
)


COPY_RUBRIC = Rubric(
    artifact_type=ArtifactType.COPY,
    items=[
        RubricItem(
            name="headlines",
            description="3+ headline variants with variety",
            weight=0.25,
            required=True,
        ),
        RubricItem(
            name="brand_voice",
            description="Copy matches brand voice guidelines",
            weight=0.25,
            required=True,
        ),
        RubricItem(
            name="ctas",
            description="Clear, action-oriented CTAs",
            weight=0.20,
            required=True,
        ),
        RubricItem(
            name="violations",
            description="No brand voice violations (avoided words)",
            weight=0.15,
        ),
        RubricItem(
            name="format",
            description="Scannable format with clear hierarchy",
            weight=0.15,
        ),
    ],
)


ACTIVATION_RUBRIC = Rubric(
    artifact_type=ArtifactType.ACTIVATION,
    items=[
        RubricItem(
            name="channels",
            description="2+ marketing channels defined with rationale",
            weight=0.25,
            required=True,
        ),
        RubricItem(
            name="budget",
            description="Budget allocation specified per channel",
            weight=0.20,
        ),
        RubricItem(
            name="calendar",
            description="Content calendar with specific dates",
            weight=0.20,
            required=True,
        ),
        RubricItem(
            name="kpis",
            description="KPIs with specific targets",
            weight=0.20,
            required=True,
        ),
        RubricItem(
            name="measurement",
            description="Measurement approach clear",
            weight=0.15,
        ),
    ],
)


VISUAL_RUBRIC = Rubric(
    artifact_type=ArtifactType.VISUAL,
    items=[
        RubricItem(
            name="concept",
            description="Clear, cohesive visual concept",
            weight=0.25,
            required=True,
        ),
        RubricItem(
            name="brand_alignment",
            description="Aligns with brand colors and style",
            weight=0.25,
            required=True,
        ),
        RubricItem(
            name="images",
            description="2+ hero images generated",
            weight=0.25,
        ),
        RubricItem(
            name="prompts",
            description="Detailed, actionable image prompts",
            weight=0.25,
        ),
    ],
)


# Registry of all rubrics
RUBRICS: dict[ArtifactType, Rubric] = {
    ArtifactType.RESEARCH: RESEARCH_RUBRIC,
    ArtifactType.STRATEGY: STRATEGY_RUBRIC,
    ArtifactType.COPY: COPY_RUBRIC,
    ArtifactType.ACTIVATION: ACTIVATION_RUBRIC,
    ArtifactType.VISUAL: VISUAL_RUBRIC,
}


def get_rubric(artifact_type: str | ArtifactType) -> Rubric | None:
    """Get rubric for an artifact type.

    Args:
        artifact_type: Type of artifact

    Returns:
        Rubric if found, None otherwise
    """
    if isinstance(artifact_type, str):
        try:
            artifact_type = ArtifactType(artifact_type)
        except ValueError:
            return None
    return RUBRICS.get(artifact_type)


@dataclass
class RubricScore:
    """Score for a single rubric item."""

    item: RubricItem
    score: float  # 0.0 to 1.0
    passed: bool
    notes: str = ""


@dataclass
class RubricResult:
    """Complete rubric evaluation result."""

    artifact_type: ArtifactType
    item_scores: list[RubricScore]
    overall_score: float
    passed: bool
    required_failures: list[str]  # Names of failed required items


def score_artifact(
    artifact_type: str | ArtifactType,
    item_scores: dict[str, float],
) -> RubricResult:
    """Score an artifact against its rubric.

    Args:
        artifact_type: Type of artifact
        item_scores: Dict mapping rubric item names to scores (0.0-1.0)

    Returns:
        RubricResult with weighted overall score
    """
    rubric = get_rubric(artifact_type)
    if not rubric:
        raise ValueError(f"Unknown artifact type: {artifact_type}")

    scores = []
    required_failures = []
    weighted_sum = 0.0

    for item in rubric.items:
        score = item_scores.get(item.name, 0.0)
        score = max(0.0, min(1.0, score))  # Clamp to 0-1

        passed = score >= 0.7
        if item.required and not passed:
            required_failures.append(item.name)

        scores.append(
            RubricScore(
                item=item,
                score=score,
                passed=passed,
            )
        )

        weighted_sum += score * item.weight

    overall_passed = (
        weighted_sum >= rubric.passing_threshold and len(required_failures) == 0
    )

    return RubricResult(
        artifact_type=rubric.artifact_type,
        item_scores=scores,
        overall_score=weighted_sum,
        passed=overall_passed,
        required_failures=required_failures,
    )


def format_rubric_for_prompt(artifact_type: str | ArtifactType) -> str:
    """Format rubric as text for LLM prompts.

    Args:
        artifact_type: Type of artifact

    Returns:
        Formatted rubric string
    """
    rubric = get_rubric(artifact_type)
    if not rubric:
        return "Apply general quality standards."

    lines = [f"{rubric.artifact_type.value.upper()} RUBRIC:"]
    for item in rubric.items:
        required = " (required)" if item.required else ""
        lines.append(f"- [ ] {item.description}{required}")

    return "\n".join(lines)
