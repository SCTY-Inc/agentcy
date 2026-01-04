"""Brand voice and claim validation.

Validates artifacts against brand guidelines and quality standards.
"""

import re
from dataclasses import dataclass
from typing import Any

from agentcy.models.brand import BrandKit


@dataclass
class ValidationResult:
    """Result of a validation check."""

    passed: bool
    score: float  # 0.0 to 1.0
    violations: list[str]
    warnings: list[str]
    details: dict[str, Any]


def validate_brand_voice(
    text: str,
    brand: BrandKit,
) -> ValidationResult:
    """Validate text against brand voice guidelines.

    Checks:
    - Tone alignment (keyword matching)
    - Avoided words/phrases
    - Style consistency

    Args:
        text: Text content to validate
        brand: Brand kit with voice guidelines

    Returns:
        ValidationResult with violations and score
    """
    violations = []
    warnings = []
    details: dict[str, Any] = {}

    text_lower = text.lower()

    # Check for avoided words/phrases
    avoided_found = []
    if brand.voice.avoid:
        for avoid in brand.voice.avoid:
            avoid_lower = avoid.lower()
            if avoid_lower in text_lower:
                avoided_found.append(avoid)
                violations.append(f"Contains avoided term: '{avoid}'")

    details["avoided_found"] = avoided_found

    # Check for tone indicators (simple keyword matching)
    tone_matches = 0
    tone_indicators = {
        "professional": ["expertise", "solution", "comprehensive", "strategic"],
        "casual": ["hey", "awesome", "cool", "check out"],
        "confident": ["guarantee", "proven", "results", "success"],
        "friendly": ["we're here", "happy to", "love to", "together"],
        "technical": ["algorithm", "implementation", "architecture", "specification"],
        "bold": ["revolutionary", "breakthrough", "transform", "disrupt"],
        "approachable": ["simple", "easy", "straightforward", "help"],
    }

    if brand.voice.tone:
        matched_tones = []
        for tone in brand.voice.tone:
            tone_lower = tone.lower()
            if tone_lower in tone_indicators:
                for indicator in tone_indicators[tone_lower]:
                    if indicator in text_lower:
                        tone_matches += 1
                        matched_tones.append(tone)
                        break
        details["tone_matches"] = matched_tones

    # Calculate score
    avoid_penalty = len(avoided_found) * 0.15  # 15% penalty per violation
    tone_bonus = min(tone_matches * 0.1, 0.3)  # Up to 30% bonus for tone alignment

    base_score = 1.0
    score = max(0.0, min(1.0, base_score - avoid_penalty + tone_bonus))

    details["avoid_penalty"] = avoid_penalty
    details["tone_bonus"] = tone_bonus

    # Add warnings for potential issues
    if len(text) < 50:
        warnings.append("Text is very short - may lack context")
    if len(text) > 5000:
        warnings.append("Text is very long - consider breaking into sections")

    # Check for common issues
    if "!!!" in text:
        warnings.append("Multiple exclamation marks may seem unprofessional")
    if text.isupper() and len(text) > 20:
        warnings.append("All caps text may seem aggressive")

    return ValidationResult(
        passed=len(violations) == 0 and score >= 0.7,
        score=score,
        violations=violations,
        warnings=warnings,
        details=details,
    )


def validate_copy_quality(
    headlines: list[str],
    body_variants: list[str],
    cta_variants: list[str],
) -> ValidationResult:
    """Validate copy deck quality.

    Checks:
    - Minimum variant counts
    - Headline length
    - CTA action verbs
    - Body copy readability

    Args:
        headlines: Headline variants
        body_variants: Body copy variants
        cta_variants: CTA variants

    Returns:
        ValidationResult with issues and score
    """
    violations = []
    warnings = []
    details: dict[str, Any] = {}

    # Check counts
    if len(headlines) < 3:
        violations.append(f"Need 3+ headlines, got {len(headlines)}")
    if len(body_variants) < 2:
        warnings.append(f"Recommend 2+ body variants, got {len(body_variants)}")
    if len(cta_variants) < 2:
        warnings.append(f"Recommend 2+ CTA variants, got {len(cta_variants)}")

    details["headline_count"] = len(headlines)
    details["body_count"] = len(body_variants)
    details["cta_count"] = len(cta_variants)

    # Check headline length
    long_headlines = [h for h in headlines if len(h.split()) > 12]
    if long_headlines:
        warnings.append(f"{len(long_headlines)} headlines exceed 12 words")
    details["long_headlines"] = len(long_headlines)

    # Check CTAs for action verbs
    action_verbs = [
        "get", "start", "try", "discover", "learn", "join", "download",
        "subscribe", "sign", "buy", "order", "claim", "unlock", "access",
    ]
    weak_ctas = []
    for cta in cta_variants:
        cta_lower = cta.lower()
        has_action = any(verb in cta_lower for verb in action_verbs)
        if not has_action:
            weak_ctas.append(cta)

    if weak_ctas:
        warnings.append(f"{len(weak_ctas)} CTAs lack strong action verbs")
    details["weak_ctas"] = weak_ctas

    # Calculate score
    base_score = 1.0
    if len(headlines) < 3:
        base_score -= 0.2
    if len(body_variants) < 2:
        base_score -= 0.1
    if len(cta_variants) < 2:
        base_score -= 0.1
    if long_headlines:
        base_score -= 0.05 * len(long_headlines)
    if weak_ctas:
        base_score -= 0.05 * len(weak_ctas)

    score = max(0.0, min(1.0, base_score))

    return ValidationResult(
        passed=len(violations) == 0 and score >= 0.7,
        score=score,
        violations=violations,
        warnings=warnings,
        details=details,
    )


def validate_research_quality(
    sources: list[dict[str, Any]],
    insights: list[str],
    competitors: list[dict[str, Any]],
) -> ValidationResult:
    """Validate research report quality.

    Args:
        sources: List of source citations
        insights: List of insights
        competitors: List of competitor analyses

    Returns:
        ValidationResult with issues and score
    """
    violations = []
    warnings = []
    details: dict[str, Any] = {}

    # Check counts
    if len(sources) < 5:
        violations.append(f"Need 5+ sources, got {len(sources)}")
    if len(insights) < 3:
        violations.append(f"Need 3+ insights, got {len(insights)}")
    if len(competitors) < 1:
        warnings.append("No competitor analysis included")

    details["source_count"] = len(sources)
    details["insight_count"] = len(insights)
    details["competitor_count"] = len(competitors)

    # Check source validity (has URL)
    valid_sources = [s for s in sources if s.get("url")]
    if len(valid_sources) < len(sources):
        warnings.append(f"{len(sources) - len(valid_sources)} sources missing URLs")

    # Calculate score
    base_score = 1.0
    if len(sources) < 5:
        base_score -= 0.2 * (5 - len(sources)) / 5
    if len(insights) < 3:
        base_score -= 0.2 * (3 - len(insights)) / 3
    if len(competitors) < 1:
        base_score -= 0.1

    score = max(0.0, min(1.0, base_score))

    return ValidationResult(
        passed=len(violations) == 0 and score >= 0.7,
        score=score,
        violations=violations,
        warnings=warnings,
        details=details,
    )


def validate_strategy_quality(
    positioning: str,
    messaging_pillars: list[str],
    proof_points: list[str],
) -> ValidationResult:
    """Validate strategy brief quality.

    Args:
        positioning: Positioning statement
        messaging_pillars: List of messaging pillars
        proof_points: List of proof points

    Returns:
        ValidationResult with issues and score
    """
    violations = []
    warnings = []
    details: dict[str, Any] = {}

    # Check positioning
    if not positioning or len(positioning) < 20:
        violations.append("Positioning statement too short or missing")
    elif len(positioning) > 500:
        warnings.append("Positioning statement is long - consider condensing")

    details["positioning_length"] = len(positioning) if positioning else 0

    # Check pillars
    if len(messaging_pillars) < 3:
        violations.append(f"Need 3+ messaging pillars, got {len(messaging_pillars)}")

    details["pillar_count"] = len(messaging_pillars)

    # Check proof points
    if len(proof_points) < len(messaging_pillars):
        warnings.append("Fewer proof points than pillars - consider adding more")

    details["proof_point_count"] = len(proof_points)

    # Calculate score
    base_score = 1.0
    if not positioning or len(positioning) < 20:
        base_score -= 0.3
    if len(messaging_pillars) < 3:
        base_score -= 0.2 * (3 - len(messaging_pillars)) / 3
    if len(proof_points) < len(messaging_pillars):
        base_score -= 0.1

    score = max(0.0, min(1.0, base_score))

    return ValidationResult(
        passed=len(violations) == 0 and score >= 0.7,
        score=score,
        violations=violations,
        warnings=warnings,
        details=details,
    )
