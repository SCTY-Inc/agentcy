"""Stage modules for agency pipeline."""

# Re-export schemas for backwards compatibility
from agency.schemas import (
    ActivationResult,
    CreativeResult,
    ResearchResult,
    StrategyResult,
)
from agency.stages.activation import run as activate
from agency.stages.creative import run as creative
from agency.stages.research import run as research
from agency.stages.strategy import run as strategy

__all__ = [
    "research",
    "strategy",
    "creative",
    "activate",
    "ResearchResult",
    "StrategyResult",
    "CreativeResult",
    "ActivationResult",
]
