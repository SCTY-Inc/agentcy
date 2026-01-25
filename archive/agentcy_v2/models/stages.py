"""Campaign stage definitions and transition rules."""

from enum import Enum


class Stage(str, Enum):
    """Campaign workflow stages."""

    INTAKE = "intake"
    RESEARCH = "research"
    STRATEGY = "strategy"
    CREATIVE = "creative"
    ACTIVATION = "activation"
    PACKAGING = "packaging"
    DONE = "done"


# Ordered stage list
STAGE_ORDER = [
    Stage.INTAKE,
    Stage.RESEARCH,
    Stage.STRATEGY,
    Stage.CREATIVE,
    Stage.ACTIVATION,
    Stage.PACKAGING,
    Stage.DONE,
]

# Valid transitions: stage -> allowed next stages
TRANSITIONS: dict[Stage, list[Stage]] = {
    Stage.INTAKE: [Stage.RESEARCH],
    Stage.RESEARCH: [Stage.STRATEGY],
    Stage.STRATEGY: [Stage.CREATIVE],
    Stage.CREATIVE: [Stage.ACTIVATION],
    Stage.ACTIVATION: [Stage.PACKAGING],
    Stage.PACKAGING: [Stage.DONE],
    Stage.DONE: [],  # Terminal state
}


class StageTransitionError(Exception):
    """Invalid stage transition attempted."""

    def __init__(self, current: Stage, target: Stage):
        self.current = current
        self.target = target
        allowed = TRANSITIONS.get(current, [])
        allowed_str = ", ".join(s.value for s in allowed) if allowed else "none"
        super().__init__(
            f"Cannot transition from {current.value} to {target.value}. "
            f"Allowed: {allowed_str}"
        )


def next_stage(current: Stage) -> Stage | None:
    """Get the next stage in the workflow.

    Args:
        current: Current stage

    Returns:
        Next stage, or None if at DONE
    """
    try:
        idx = STAGE_ORDER.index(current)
        if idx + 1 < len(STAGE_ORDER):
            return STAGE_ORDER[idx + 1]
    except ValueError:
        pass
    return None


def can_transition(current: Stage, target: Stage) -> bool:
    """Check if transition is valid.

    Args:
        current: Current stage
        target: Target stage

    Returns:
        True if transition is allowed
    """
    return target in TRANSITIONS.get(current, [])


def validate_transition(current: Stage, target: Stage) -> None:
    """Validate and raise if transition is invalid.

    Args:
        current: Current stage
        target: Target stage

    Raises:
        StageTransitionError: If transition not allowed
    """
    if not can_transition(current, target):
        raise StageTransitionError(current, target)
