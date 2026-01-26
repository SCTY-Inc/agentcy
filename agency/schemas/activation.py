"""Activation stage schemas."""

from pydantic import BaseModel, Field


class Channel(BaseModel):
    """Marketing channel plan."""

    name: str
    objective: str
    tactics: list[str] = Field(default_factory=list)
    budget_pct: float = Field(ge=0.0, le=1.0, default=0.25)


class CalendarEntry(BaseModel):
    """Content calendar item."""

    week: int
    channel: str
    content_type: str
    description: str


class KPI(BaseModel):
    """Key performance indicator."""

    metric: str
    target: str
    measurement: str


class ActivationResult(BaseModel):
    """Output of activation stage."""

    channels: list[Channel] = Field(default_factory=list)
    calendar: list[CalendarEntry] = Field(default_factory=list)
    kpis: list[KPI] = Field(default_factory=list)
    budget_split: dict[str, float] = Field(default_factory=dict)
