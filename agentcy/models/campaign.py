"""Campaign state model for persistence."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from agentcy.models.stages import Stage


class StageResult(BaseModel):
    """Result of a completed stage."""

    stage: Stage
    artifact: dict[str, Any]
    approved: bool = False
    approved_at: datetime | None = None
    inputs_hash: str | None = None  # For idempotency


class Campaign(BaseModel):
    """Campaign state persisted to SQLite."""

    id: str
    brief: str
    brand_name: str | None = None
    template: str = "product-launch"
    current_stage: Stage = Stage.INTAKE
    results: dict[str, StageResult] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    total_tokens: int = 0
    total_cost_usd: float = 0.0
