"""SEO analysis plugin.

Analyzes research results for SEO opportunities.

Usage:
    agency seo < research.json
    agency research "brief" | agency seo
"""

from pydantic import BaseModel, Field

from agency.core.llm import generate
from agency.plugins import register
from agency.schemas import ResearchResult


class Keyword(BaseModel):
    """Target keyword."""

    keyword: str
    intent: str  # informational, transactional, navigational
    difficulty: str  # low, medium, high
    priority: int = Field(ge=1, le=5)


class SEOResult(BaseModel):
    """Output of SEO analysis."""

    target_keywords: list[Keyword] = Field(default_factory=list)
    content_gaps: list[str] = Field(default_factory=list)
    title_suggestions: list[str] = Field(default_factory=list)
    meta_descriptions: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


SYSTEM = """You are an SEO expert analyzing market research for search optimization opportunities.

Your role:
- Identify target keywords with search intent
- Find content gaps competitors aren't addressing
- Suggest optimized titles and meta descriptions
- Provide actionable SEO recommendations

Focus on realistic, achievable rankings."""


@register("seo", "SEO keyword and content analysis", SEOResult, ResearchResult)
def run(research: ResearchResult) -> SEOResult:
    """Execute SEO analysis.

    Args:
        research: ResearchResult from research stage

    Returns:
        SEOResult with keywords, content gaps, recommendations
    """
    insights_ctx = "\n".join(f"- {i}" for i in research.insights[:10])
    competitors_ctx = "\n".join(f"- {c.name}: {c.positioning}" for c in research.competitors[:5])

    prompt = f"""Analyze this market research for SEO opportunities.

BRIEF:
{research.brief}

KEY INSIGHTS:
{insights_ctx}

COMPETITORS:
{competitors_ctx}

Provide:
1. 5-10 target keywords with intent and difficulty
2. Content gaps not being addressed by competitors
3. 3-5 optimized title tag suggestions
4. 3-5 meta description suggestions (under 160 chars each)
5. Actionable SEO recommendations"""

    return generate(prompt=prompt, schema=SEOResult, system=SYSTEM)
