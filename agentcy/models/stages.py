"""Campaign stage definitions and exit criteria."""

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


# Stage transitions
STAGE_ORDER = [
    Stage.INTAKE,
    Stage.RESEARCH,
    Stage.STRATEGY,
    Stage.CREATIVE,
    Stage.ACTIVATION,
    Stage.PACKAGING,
    Stage.DONE,
]
