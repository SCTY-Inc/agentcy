"""Campaign state machine controller.

Custom orchestrator (NOT Agno Workflows) that manages:
    - Stage transitions: INTAKE -> RESEARCH -> STRATEGY -> CREATIVE -> ACTIVATION -> PACKAGING -> DONE
    - Human gates at each transition (approve/edit/regen)
    - Persistence to SQLite
    - Resume capability
"""
