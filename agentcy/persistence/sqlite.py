"""SQLite storage for campaign state and Agno Culture.

Provides durable storage for:
- Campaign metadata and current stage
- Stage results with approval status
- Resume capability across sessions
"""

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator

from agentcy.models.campaign import Campaign, StageResult
from agentcy.models.stages import Stage


class CampaignStore:
    """SQLite-backed campaign storage."""

    def __init__(self, db_path: Path | str = "agentcy.db"):
        """Initialize the campaign store.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self._init_schema()

    def _init_schema(self) -> None:
        """Create database tables if they don't exist."""
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS campaigns (
                    id TEXT PRIMARY KEY,
                    brief TEXT NOT NULL,
                    brand_name TEXT,
                    template TEXT DEFAULT 'product-launch',
                    current_stage TEXT DEFAULT 'intake',
                    total_tokens INTEGER DEFAULT 0,
                    total_cost_usd REAL DEFAULT 0.0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS stage_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    campaign_id TEXT NOT NULL,
                    stage TEXT NOT NULL,
                    artifact TEXT NOT NULL,  -- JSON blob
                    approved INTEGER DEFAULT 0,
                    approved_at TEXT,
                    inputs_hash TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (campaign_id) REFERENCES campaigns(id),
                    UNIQUE(campaign_id, stage)
                );

                CREATE INDEX IF NOT EXISTS idx_stage_results_campaign
                ON stage_results(campaign_id);
                """
            )

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def save(self, campaign: Campaign) -> None:
        """Save or update a campaign.

        Args:
            campaign: Campaign to save
        """
        with self._connect() as conn:
            # Upsert campaign
            conn.execute(
                """
                INSERT INTO campaigns (
                    id, brief, brand_name, template, current_stage,
                    total_tokens, total_cost_usd, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    brief = excluded.brief,
                    brand_name = excluded.brand_name,
                    template = excluded.template,
                    current_stage = excluded.current_stage,
                    total_tokens = excluded.total_tokens,
                    total_cost_usd = excluded.total_cost_usd,
                    updated_at = excluded.updated_at
                """,
                (
                    campaign.id,
                    campaign.brief,
                    campaign.brand_name,
                    campaign.template,
                    campaign.current_stage.value,
                    campaign.total_tokens,
                    campaign.total_cost_usd,
                    campaign.created_at.isoformat(),
                    campaign.updated_at.isoformat(),
                ),
            )

            # Save stage results
            for stage_name, result in campaign.results.items():
                self._save_stage_result(conn, campaign.id, result)

    def _save_stage_result(
        self, conn: sqlite3.Connection, campaign_id: str, result: StageResult
    ) -> None:
        """Save a stage result."""
        conn.execute(
            """
            INSERT INTO stage_results (
                campaign_id, stage, artifact, approved, approved_at, inputs_hash, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(campaign_id, stage) DO UPDATE SET
                artifact = excluded.artifact,
                approved = excluded.approved,
                approved_at = excluded.approved_at,
                inputs_hash = excluded.inputs_hash
            """,
            (
                campaign_id,
                result.stage.value,
                json.dumps(result.artifact, default=str),
                1 if result.approved else 0,
                result.approved_at.isoformat() if result.approved_at else None,
                result.inputs_hash,
                datetime.now().isoformat(),
            ),
        )

    def load(self, campaign_id: str) -> Campaign | None:
        """Load a campaign by ID.

        Args:
            campaign_id: Campaign ID to load

        Returns:
            Campaign if found, None otherwise
        """
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM campaigns WHERE id = ?", (campaign_id,)
            ).fetchone()

            if not row:
                return None

            # Load stage results
            result_rows = conn.execute(
                "SELECT * FROM stage_results WHERE campaign_id = ?", (campaign_id,)
            ).fetchall()

            results = {}
            for r in result_rows:
                stage = Stage(r["stage"])
                results[r["stage"]] = StageResult(
                    stage=stage,
                    artifact=json.loads(r["artifact"]),
                    approved=bool(r["approved"]),
                    approved_at=(
                        datetime.fromisoformat(r["approved_at"])
                        if r["approved_at"]
                        else None
                    ),
                    inputs_hash=r["inputs_hash"],
                )

            return Campaign(
                id=row["id"],
                brief=row["brief"],
                brand_name=row["brand_name"],
                template=row["template"],
                current_stage=Stage(row["current_stage"]),
                results=results,
                total_tokens=row["total_tokens"],
                total_cost_usd=row["total_cost_usd"],
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
            )

    def list_campaigns(
        self, limit: int = 20, include_done: bool = True
    ) -> list[dict[str, Any]]:
        """List recent campaigns.

        Args:
            limit: Maximum number to return
            include_done: Include completed campaigns

        Returns:
            List of campaign summaries
        """
        with self._connect() as conn:
            query = "SELECT id, brief, current_stage, updated_at FROM campaigns"
            params: list[Any] = []

            if not include_done:
                query += " WHERE current_stage != ?"
                params.append(Stage.DONE.value)

            query += " ORDER BY updated_at DESC LIMIT ?"
            params.append(limit)

            rows = conn.execute(query, params).fetchall()

            return [
                {
                    "id": r["id"],
                    "brief": r["brief"][:50] + "..." if len(r["brief"]) > 50 else r["brief"],
                    "stage": r["current_stage"],
                    "updated": r["updated_at"],
                }
                for r in rows
            ]

    def delete(self, campaign_id: str) -> bool:
        """Delete a campaign and its results.

        Args:
            campaign_id: Campaign to delete

        Returns:
            True if deleted, False if not found
        """
        with self._connect() as conn:
            # Delete stage results first (FK constraint)
            conn.execute(
                "DELETE FROM stage_results WHERE campaign_id = ?", (campaign_id,)
            )
            result = conn.execute(
                "DELETE FROM campaigns WHERE id = ?", (campaign_id,)
            )
            return result.rowcount > 0

    def get_in_progress(self) -> list[Campaign]:
        """Get all campaigns that are not complete.

        Returns:
            List of in-progress campaigns
        """
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id FROM campaigns WHERE current_stage != ?",
                (Stage.DONE.value,),
            ).fetchall()

            campaigns = []
            for row in rows:
                campaign = self.load(row["id"])
                if campaign:
                    campaigns.append(campaign)
            return campaigns

    def update_stage(self, campaign_id: str, stage: Stage) -> None:
        """Update just the current stage of a campaign.

        Args:
            campaign_id: Campaign to update
            stage: New current stage
        """
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE campaigns
                SET current_stage = ?, updated_at = ?
                WHERE id = ?
                """,
                (stage.value, datetime.now().isoformat(), campaign_id),
            )

    def update_cost(
        self, campaign_id: str, tokens: int, cost_usd: float
    ) -> None:
        """Add token/cost usage to campaign.

        Args:
            campaign_id: Campaign to update
            tokens: Tokens to add
            cost_usd: Cost to add
        """
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE campaigns
                SET total_tokens = total_tokens + ?,
                    total_cost_usd = total_cost_usd + ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (tokens, cost_usd, datetime.now().isoformat(), campaign_id),
            )


# Module-level convenience functions


_default_store: CampaignStore | None = None


def get_store(db_path: Path | str | None = None) -> CampaignStore:
    """Get the default campaign store.

    Args:
        db_path: Optional path to database file

    Returns:
        CampaignStore instance
    """
    global _default_store
    if db_path is not None:
        return CampaignStore(db_path)
    if _default_store is None:
        _default_store = CampaignStore()
    return _default_store


def save_campaign(campaign: Campaign, db_path: Path | str | None = None) -> None:
    """Save a campaign to the database.

    Args:
        campaign: Campaign to save
        db_path: Optional database path
    """
    get_store(db_path).save(campaign)


def load_campaign(
    campaign_id: str, db_path: Path | str | None = None
) -> Campaign | None:
    """Load a campaign from the database.

    Args:
        campaign_id: ID of campaign to load
        db_path: Optional database path

    Returns:
        Campaign if found, None otherwise
    """
    return get_store(db_path).load(campaign_id)
