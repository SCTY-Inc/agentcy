"""Database path configuration.

Simple module for consistent database path handling.
Campaign persistence uses SQLModel directly.
"""

from pathlib import Path

# Default database path
DEFAULT_DB_PATH = Path("agentcy.db")


def get_db_path(db_path: Path | str | None = None) -> Path:
    """Get database path.

    Args:
        db_path: Optional database path. Uses default if not provided.

    Returns:
        Path to database file
    """
    if db_path is not None:
        return Path(db_path)
    return DEFAULT_DB_PATH
