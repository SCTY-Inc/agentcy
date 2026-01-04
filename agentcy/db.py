"""Shared database for campaigns and Agno Culture.

Single SQLite database used by:
- CampaignStore for campaign state
- CultureManager for shared knowledge
- Agents with add_culture_to_context=True
"""

from pathlib import Path

from agno.db.sqlite import SqliteDb

# Default database path
DEFAULT_DB_PATH = Path("agentcy.db")

# Module-level singleton for Agno DB
_agno_db: SqliteDb | None = None


def get_agno_db(db_path: Path | str | None = None) -> SqliteDb:
    """Get shared Agno SqliteDb instance.

    This is the same database used by CampaignStore, ensuring
    Culture and campaign state are co-located.

    Args:
        db_path: Optional database path. Uses default if not provided.

    Returns:
        Agno SqliteDb instance for Culture and agent memory
    """
    global _agno_db

    if db_path is not None:
        # Explicit path requested - create new instance
        return SqliteDb(db_file=str(db_path))

    if _agno_db is None:
        _agno_db = SqliteDb(db_file=str(DEFAULT_DB_PATH))

    return _agno_db


def reset_db() -> None:
    """Reset the singleton (for testing)."""
    global _agno_db
    _agno_db = None
