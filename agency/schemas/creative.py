"""Creative stage schemas."""

from pydantic import BaseModel, Field


class CreativeResult(BaseModel):
    """Output of creative stage."""

    headlines: list[str] = Field(default_factory=list)
    body_copy: list[str] = Field(default_factory=list)
    ctas: list[str] = Field(default_factory=list)
    tagline: str = ""
