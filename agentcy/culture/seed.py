"""Seed Agno Culture with brand voice, marketing frameworks, and quality rubrics.

Culture provides shared knowledge that all agents access during reasoning.
Brand voice is seeded as read-only to prevent drift.
"""

from agno.culture.manager import CultureManager
from agno.db.schemas.culture import CulturalKnowledge
from agno.db.sqlite import SqliteDb

from agentcy.models.brand import BrandKit


def get_culture_manager(db_path: str = "agentcy.db") -> CultureManager:
    """Get a CultureManager instance with SQLite backend."""
    db = SqliteDb(db_file=db_path)
    return CultureManager(db=db)


def seed_brand_voice(manager: CultureManager, brand: BrandKit) -> None:
    """Seed brand voice guidelines as cultural knowledge.

    Brand voice is fundamental to consistent output quality.
    This is seeded manually (not via model) to ensure exact preservation.
    """
    tone_str = ", ".join(brand.voice.tone) if brand.voice.tone else "professional"
    avoid_str = ", ".join(brand.voice.avoid) if brand.voice.avoid else "none specified"

    content = f"""Brand: {brand.name}
Tagline: {brand.tagline or 'Not specified'}
Industry: {brand.industry or 'Not specified'}
Target Audience: {brand.target_audience or 'Not specified'}

Voice Guidelines:
- Tone: {tone_str}
- Avoid: {avoid_str}

Writing Rules:
- Always write in the brand's voice
- Match the tone descriptors above
- Never use phrases or styles marked as "avoid"
- Keep messaging consistent with the tagline and industry positioning
"""

    brand_voice = CulturalKnowledge(
        name=f"{brand.name} Brand Voice",
        summary=f"Voice guidelines for {brand.name}: {tone_str}",
        categories=["brand", "voice", "tone"],
        content=content,
        notes=["Seeded from brand.yaml - do not modify"],
    )

    manager.add_cultural_knowledge(brand_voice)


def seed_marketing_frameworks(manager: CultureManager) -> None:
    """Seed standard marketing frameworks as cultural knowledge."""

    frameworks = CulturalKnowledge(
        name="Marketing Frameworks",
        summary="Standard frameworks for strategy and messaging development",
        categories=["strategy", "frameworks", "marketing"],
        content="""Core Marketing Frameworks:

1. STP (Segmentation, Targeting, Positioning)
   - Segmentation: Divide market into distinct groups
   - Targeting: Select which segments to serve
   - Positioning: Define how to be perceived vs competitors

2. 4Ps (Product, Price, Place, Promotion)
   - Product: What you're selling and its features
   - Price: Pricing strategy and value proposition
   - Place: Distribution channels and availability
   - Promotion: How you communicate and advertise

3. AIDA (Attention, Interest, Desire, Action)
   - Attention: Capture with bold headlines/visuals
   - Interest: Engage with relevant benefits
   - Desire: Create emotional connection
   - Action: Clear CTA driving conversion

4. Problem-Agitate-Solution (PAS)
   - Problem: Identify the pain point
   - Agitate: Amplify the consequences
   - Solution: Present your offering as the answer

5. Features-Advantages-Benefits (FAB)
   - Features: What the product has
   - Advantages: Why features matter
   - Benefits: What customer gains

Apply these frameworks when developing strategy briefs, copy decks, and activation plans.
""",
        notes=["Standard marketing frameworks - reference only"],
    )

    manager.add_cultural_knowledge(frameworks)


def seed_quality_rubrics(manager: CultureManager) -> None:
    """Seed quality rubrics for artifact evaluation."""

    rubrics = CulturalKnowledge(
        name="Quality Rubrics",
        summary="Evaluation criteria for campaign artifacts",
        categories=["quality", "review", "standards"],
        content="""Quality Rubrics for Campaign Artifacts:

RESEARCH REPORT:
- [ ] 5+ credible sources cited
- [ ] 3+ actionable insights extracted
- [ ] Competitor analysis included
- [ ] Assumptions clearly stated
- [ ] No unsubstantiated claims

STRATEGY BRIEF:
- [ ] Clear positioning statement
- [ ] Target audience persona defined
- [ ] 3+ messaging pillars identified
- [ ] Proof points for each pillar
- [ ] Risks and mitigation noted

COPY DECK:
- [ ] 3+ headline variants
- [ ] Body copy matches brand voice
- [ ] Clear CTA in each variant
- [ ] No brand voice violations
- [ ] Scannable format (bullets, short paragraphs)

ACTIVATION PLAN:
- [ ] 2+ channels defined
- [ ] Budget allocation specified
- [ ] Content calendar with dates
- [ ] KPIs with targets
- [ ] Measurement approach clear

GENERAL QUALITY:
- Clarity: Is the message immediately understandable?
- Relevance: Does it address the target audience's needs?
- Differentiation: Does it stand out from competitors?
- Actionability: Does it drive the desired behavior?
- Consistency: Does it align with brand guidelines?
""",
        notes=["Use these rubrics when reviewing artifacts"],
    )

    manager.add_cultural_knowledge(rubrics)


def seed_copywriting_principles(manager: CultureManager) -> None:
    """Seed copywriting best practices."""

    copywriting = CulturalKnowledge(
        name="Copywriting Principles",
        summary="Best practices for persuasive marketing copy",
        categories=["copy", "writing", "persuasion"],
        content="""Copywriting Principles:

HEADLINES:
- Lead with the benefit, not the feature
- Use numbers when possible ("5 ways to...")
- Create urgency without being pushy
- Ask questions that resonate
- Keep under 10 words for impact

BODY COPY:
- Write at 8th grade reading level
- Use active voice ("Get results" not "Results can be gotten")
- One idea per paragraph
- Front-load important information
- Use "you" more than "we"

CTAs:
- Start with action verb
- Be specific ("Start free trial" not "Submit")
- Create value ("Get instant access" not "Click here")
- One primary CTA per piece

PROOF:
- Include specific numbers when available
- Use social proof (testimonials, logos, case studies)
- Address objections proactively
- Back claims with evidence

AVOID:
- Jargon and buzzwords ("synergy", "leverage", "solution")
- Passive voice
- Long sentences (aim for <20 words)
- Multiple CTAs competing for attention
- Unsupported superlatives ("best", "fastest", "only")
""",
        notes=["Apply these principles to all copy output"],
    )

    manager.add_cultural_knowledge(copywriting)


def seed_all(manager: CultureManager, brand: BrandKit | None = None) -> None:
    """Seed all cultural knowledge.

    Args:
        manager: CultureManager instance
        brand: Optional brand kit to seed voice from
    """
    # Always seed frameworks and rubrics
    seed_marketing_frameworks(manager)
    seed_quality_rubrics(manager)
    seed_copywriting_principles(manager)

    # Seed brand voice if provided
    if brand:
        seed_brand_voice(manager, brand)
