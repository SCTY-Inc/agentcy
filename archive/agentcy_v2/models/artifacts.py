"""Pydantic schemas for campaign artifacts.

Each stage produces typed artifacts that can be validated,
serialized, and exported.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class Source(BaseModel):
    """Research source reference."""

    url: str
    title: str
    snippet: str | None = None


class CompetitorAnalysis(BaseModel):
    """Competitor intelligence."""

    name: str
    positioning: str
    strengths: list[str]
    weaknesses: list[str]


class ResearchReport(BaseModel):
    """Output of RESEARCH stage."""

    campaign_id: str
    sources: list[Source] = Field(default_factory=list)
    insights: list[str] = Field(default_factory=list)
    competitors: list[CompetitorAnalysis] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)


class AudiencePersona(BaseModel):
    """Target audience definition."""

    name: str
    demographics: str
    pain_points: list[str]
    motivations: list[str]


class StrategyBrief(BaseModel):
    """Output of STRATEGY stage."""

    campaign_id: str
    positioning: str
    target_audience: AudiencePersona
    messaging_pillars: list[str]
    proof_points: list[str]
    risks: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)


class CopyDeck(BaseModel):
    """Output of CREATIVE stage (copy)."""

    campaign_id: str
    headline_variants: list[str]
    body_variants: list[str]
    cta_variants: list[str]
    brand_voice_score: float = Field(ge=0.0, le=1.0)
    created_at: datetime = Field(default_factory=datetime.now)


class ChannelPlan(BaseModel):
    """Single channel activation plan."""

    channel: str
    objective: str
    tactics: list[str]
    budget_pct: float = Field(ge=0.0, le=1.0)


class CalendarEntry(BaseModel):
    """Content calendar item."""

    date: str
    channel: str
    content_type: str
    description: str


class KPI(BaseModel):
    """Key performance indicator."""

    metric: str
    target: str
    measurement: str


class ActivationPlan(BaseModel):
    """Output of ACTIVATION stage."""

    campaign_id: str
    channels: list[ChannelPlan]
    content_calendar: list[CalendarEntry] = Field(default_factory=list)
    budget_allocation: dict[str, float] = Field(default_factory=dict)
    kpis: list[KPI] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
