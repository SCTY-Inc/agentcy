"""Stage modules for agency pipeline."""

from agency.stages.activation import ActivationResult
from agency.stages.activation import run as activate
from agency.stages.creative import CreativeResult
from agency.stages.creative import run as creative
from agency.stages.research import ResearchResult
from agency.stages.research import run as research
from agency.stages.strategy import StrategyResult
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
