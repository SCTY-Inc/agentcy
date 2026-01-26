"""Strategy stage schemas."""

from pydantic import BaseModel, Field


class Persona(BaseModel):
    """Target audience persona."""

    name: str
    demographics: str
    pain_points: list[str] = Field(default_factory=list)
    motivations: list[str] = Field(default_factory=list)


class StrategyResult(BaseModel):
    """Output of strategy stage."""

    positioning: str
    target_audience: Persona
    messaging_pillars: list[str] = Field(default_factory=list)
    proof_points: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
