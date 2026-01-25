"""JSON file storage for interactive mode resume.

Stores campaign state as JSON files in .agency/ directory.
"""

from datetime import datetime
from pathlib import Path

from pydantic import BaseModel


class CampaignState(BaseModel):
    """Campaign state for resume support."""

    id: str
    brief: str
    stage: str = "research"  # research, strategy, creative, activation, done
    research: dict | None = None
    strategy: dict | None = None
    creative: dict | None = None
    activation: dict | None = None
    created_at: str = ""
    updated_at: str = ""


class Store:
    """JSON file store for interactive mode."""

    def __init__(self, base_dir: str = ".agency"):
        self.base = Path(base_dir)
        self.base.mkdir(exist_ok=True)

    def _path(self, campaign_id: str) -> Path:
        return self.base / f"{campaign_id}.json"

    def create(self, campaign_id: str, brief: str) -> CampaignState:
        """Create new campaign."""
        now = datetime.now().isoformat()
        state = CampaignState(
            id=campaign_id,
            brief=brief,
            created_at=now,
            updated_at=now,
        )
        self._save(state)
        return state

    def get(self, campaign_id: str) -> CampaignState | None:
        """Get campaign by ID."""
        path = self._path(campaign_id)
        if not path.exists():
            return None
        return CampaignState.model_validate_json(path.read_text())

    def list_all(self) -> list[CampaignState]:
        """List all campaigns."""
        campaigns = []
        for f in self.base.glob("*.json"):
            try:
                campaigns.append(CampaignState.model_validate_json(f.read_text()))
            except Exception:
                continue
        return sorted(campaigns, key=lambda c: c.updated_at, reverse=True)

    def save_stage(self, campaign_id: str, stage: str, result: BaseModel, next_stage: str) -> None:
        """Save stage result and advance."""
        state = self.get(campaign_id)
        if not state:
            raise ValueError(f"Campaign {campaign_id} not found")

        setattr(state, stage, result.model_dump())
        state.stage = next_stage
        state.updated_at = datetime.now().isoformat()
        self._save(state)

    def load_stage(self, campaign_id: str, stage: str, schema: type[BaseModel]) -> BaseModel | None:
        """Load stage result."""
        state = self.get(campaign_id)
        if not state:
            return None
        data = getattr(state, stage, None)
        if data:
            return schema.model_validate(data)
        return None

    def delete(self, campaign_id: str) -> bool:
        """Delete campaign."""
        path = self._path(campaign_id)
        if path.exists():
            path.unlink()
            return True
        return False

    def _save(self, state: CampaignState) -> None:
        """Save state to file."""
        self._path(state.id).write_text(state.model_dump_json(indent=2))


def get_store(base_dir: str = ".agency") -> Store:
    """Get store instance."""
    return Store(base_dir)
