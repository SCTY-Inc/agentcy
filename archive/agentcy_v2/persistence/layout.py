"""Campaign output directory layout specification.

Defines the standard directory structure for campaign artifacts:

    campaigns/
    └── <campaign-id>/
        ├── campaign.json          # Campaign state (resumable)
        ├── research/
        │   ├── report.md          # Research report
        │   └── sources.json       # Source citations
        ├── strategy/
        │   ├── brief.md           # Strategy brief
        │   └── personas.json      # Audience personas
        ├── creative/
        │   ├── copy.md            # Copy deck
        │   ├── headlines.json     # Headline variants
        │   └── visuals/           # Generated images
        ├── activation/
        │   ├── plan.md            # Activation plan
        │   ├── calendar.csv       # Content calendar
        │   └── budget.json        # Budget allocation
        └── package/
            ├── deck.md            # Final presentation
            └── assets/            # Exported assets
"""

import json
from pathlib import Path
from typing import Any


class CampaignLayout:
    """Manages campaign directory structure and file I/O."""

    def __init__(self, campaign_dir: Path):
        """Initialize layout for a campaign directory.

        Args:
            campaign_dir: Root directory for this campaign
        """
        self.root = campaign_dir
        self._ensure_structure()

    def _ensure_structure(self) -> None:
        """Create the standard directory structure."""
        dirs = [
            self.root,
            self.root / "research",
            self.root / "strategy",
            self.root / "creative",
            self.root / "creative" / "visuals",
            self.root / "activation",
            self.root / "package",
            self.root / "package" / "assets",
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)

    # State file
    @property
    def state_file(self) -> Path:
        return self.root / "campaign.json"

    # Research stage
    @property
    def research_report(self) -> Path:
        return self.root / "research" / "report.md"

    @property
    def research_sources(self) -> Path:
        return self.root / "research" / "sources.json"

    # Strategy stage
    @property
    def strategy_brief(self) -> Path:
        return self.root / "strategy" / "brief.md"

    @property
    def strategy_personas(self) -> Path:
        return self.root / "strategy" / "personas.json"

    # Creative stage
    @property
    def copy_deck(self) -> Path:
        return self.root / "creative" / "copy.md"

    @property
    def headlines(self) -> Path:
        return self.root / "creative" / "headlines.json"

    @property
    def visuals_dir(self) -> Path:
        return self.root / "creative" / "visuals"

    # Activation stage
    @property
    def activation_plan(self) -> Path:
        return self.root / "activation" / "plan.md"

    @property
    def content_calendar(self) -> Path:
        return self.root / "activation" / "calendar.csv"

    @property
    def budget(self) -> Path:
        return self.root / "activation" / "budget.json"

    # Package stage
    @property
    def final_deck(self) -> Path:
        return self.root / "package" / "deck.md"

    @property
    def package_brief(self) -> Path:
        return self.root / "package" / "brief.md"

    @property
    def assets_dir(self) -> Path:
        return self.root / "package" / "assets"

    # Utility methods
    def write_json(self, path: Path, data: Any) -> None:
        """Write JSON data to file."""
        path.write_text(json.dumps(data, indent=2, default=str))

    def read_json(self, path: Path) -> Any:
        """Read JSON data from file."""
        if not path.exists():
            return None
        return json.loads(path.read_text())

    def write_markdown(self, path: Path, content: str) -> None:
        """Write markdown content to file."""
        path.write_text(content)

    def read_markdown(self, path: Path) -> str | None:
        """Read markdown content from file."""
        if not path.exists():
            return None
        return path.read_text()


def generate_campaign_id() -> str:
    """Generate a unique campaign ID.

    Format: YYYYMMDD-HHMMSS-XXXX where XXXX is random hex.
    """
    import secrets
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    suffix = secrets.token_hex(2)
    return f"{timestamp}-{suffix}"


def get_campaign_layout(
    output_dir: Path,
    campaign_id: str | None = None,
) -> CampaignLayout:
    """Get or create a campaign layout.

    Args:
        output_dir: Parent directory for campaigns
        campaign_id: Existing campaign ID, or None to generate new

    Returns:
        CampaignLayout for the campaign directory
    """
    if campaign_id is None:
        campaign_id = generate_campaign_id()

    campaign_dir = output_dir / campaign_id
    return CampaignLayout(campaign_dir)
