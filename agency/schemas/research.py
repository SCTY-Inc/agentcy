"""Research stage schemas."""

from pydantic import BaseModel, Field


class Source(BaseModel):
    """Research source reference."""

    url: str
    title: str
    snippet: str = ""


class Competitor(BaseModel):
    """Competitor analysis."""

    name: str
    positioning: str
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)


class ResearchResult(BaseModel):
    """Output of research stage."""

    brief: str
    insights: list[str] = Field(default_factory=list)
    competitors: list[Competitor] = Field(default_factory=list)
    sources: list[Source] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
