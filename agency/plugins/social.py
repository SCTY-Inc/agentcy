"""Social media content plugin.

Generates platform-specific social content from creative.

Usage:
    agency social < creative.json
    agency creative < strategy.json | agency social
"""

from pydantic import BaseModel, Field

from agency.core.llm import generate
from agency.plugins import register
from agency.schemas import CreativeResult


class SocialPost(BaseModel):
    """Social media post."""

    platform: str  # twitter, linkedin, instagram, tiktok
    content: str
    hashtags: list[str] = Field(default_factory=list)
    cta: str = ""
    format_notes: str = ""  # e.g., "carousel", "thread", "reel"


class SocialResult(BaseModel):
    """Output of social content generation."""

    posts: list[SocialPost] = Field(default_factory=list)
    content_calendar_notes: list[str] = Field(default_factory=list)
    platform_recommendations: list[str] = Field(default_factory=list)


SYSTEM = """You are a social media content strategist.

Your role:
- Create platform-native content (not repurposed)
- Match platform voice and format constraints
- Include relevant hashtags for discovery
- Suggest content formats (carousels, threads, reels)

Platform specifics:
- Twitter/X: 280 chars, threads for depth, conversational
- LinkedIn: Professional, 1300 chars, thought leadership
- Instagram: Visual-first, carousel for education, 2200 chars
- TikTok: Trend-aware, hook in first 3 seconds, casual"""


@register("social", "Platform-specific social content", SocialResult, CreativeResult)
def run(creative: CreativeResult) -> SocialResult:
    """Generate social media content.

    Args:
        creative: CreativeResult from creative stage

    Returns:
        SocialResult with platform-specific posts
    """
    headlines_ctx = "\n".join(f"- {h}" for h in creative.headlines[:5])
    copy_ctx = "\n".join(f"- {c}" for c in creative.body_copy[:3])

    prompt = f"""Create social media content from this creative.

HEADLINES:
{headlines_ctx}

BODY COPY:
{copy_ctx}

TAGLINE:
{creative.tagline}

CTAs:
{", ".join(creative.ctas[:3])}

Generate:
1. 2 posts per platform (Twitter, LinkedIn, Instagram, TikTok)
2. Platform-appropriate hashtags
3. Content calendar notes for posting cadence
4. Platform prioritization recommendations"""

    return generate(prompt=prompt, schema=SocialResult, system=SYSTEM)
