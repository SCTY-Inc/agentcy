"""Agency - AI marketing campaign generator.

Agent-first by default. Human-in-the-loop optional.

Usage:
    # Full pipeline
    result = run("Launch AI product to devs")

    # Individual stages
    r = research("AI dev tools market")
    s = strategy(r)
    c = creative(s)
    a = activate(s, c)

    # Plugins
    from agency import plugins
    seo_result = plugins.run_plugin("seo", r)

    # With HITL (CLI only)
    agency run "Brief" --interactive
"""

from agency.schemas import (
    SCHEMAS,
    ActivationResult,
    CreativeResult,
    ResearchResult,
    StrategyResult,
)
from agency.stages import (
    activate,
    creative,
    research,
    strategy,
)


def run(
    brief: str,
    interactive: bool = False,
) -> dict:
    """Run full campaign pipeline.

    Args:
        brief: Campaign brief
        interactive: Enable HITL gates (CLI only, ignored in API)

    Returns:
        Dict with research, strategy, creative, activation results
    """
    if interactive:
        raise ValueError("interactive=True only supported via CLI: agency run --interactive")

    r = research(brief)
    s = strategy(r)
    c = creative(s)
    a = activate(s, c)

    return {
        "brief": brief,
        "research": r.model_dump(),
        "strategy": s.model_dump(),
        "creative": c.model_dump(),
        "activation": a.model_dump(),
    }


__all__ = [
    "run",
    "research",
    "strategy",
    "creative",
    "activate",
    "ResearchResult",
    "StrategyResult",
    "CreativeResult",
    "ActivationResult",
    "SCHEMAS",
]
