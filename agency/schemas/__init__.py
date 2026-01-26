"""Domain schema registry - ubiquitous language for agency pipeline.

All Pydantic models defining the contract between stages.
Import from here, not from individual stage modules.
"""

from agency.schemas.activation import KPI, ActivationResult, CalendarEntry, Channel
from agency.schemas.creative import CreativeResult
from agency.schemas.research import Competitor, ResearchResult, Source
from agency.schemas.strategy import Persona, StrategyResult

# Schema registry for dynamic lookup
SCHEMAS: dict[str, type] = {
    "research": ResearchResult,
    "strategy": StrategyResult,
    "creative": CreativeResult,
    "activation": ActivationResult,
}

__all__ = [
    # Research
    "Source",
    "Competitor",
    "ResearchResult",
    # Strategy
    "Persona",
    "StrategyResult",
    # Creative
    "CreativeResult",
    # Activation
    "Channel",
    "CalendarEntry",
    "KPI",
    "ActivationResult",
    # Registry
    "SCHEMAS",
]
