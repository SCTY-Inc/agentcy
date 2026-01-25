"""Brand kit schema for Agno Culture seeding."""

from pydantic import BaseModel, Field


class VoiceGuidelines(BaseModel):
    """Brand voice configuration."""

    tone: list[str] = Field(default_factory=list)
    avoid: list[str] = Field(default_factory=list)
    examples_file: str | None = None


class BrandKit(BaseModel):
    """Brand configuration loaded from brand.yaml."""

    name: str
    tagline: str | None = None
    industry: str | None = None
    competitors: list[str] = Field(default_factory=list)
    target_audience: str | None = None
    voice: VoiceGuidelines = Field(default_factory=VoiceGuidelines)
    colors: list[str] = Field(default_factory=list)
    fonts: list[str] = Field(default_factory=list)
