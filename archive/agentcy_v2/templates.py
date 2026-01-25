"""Campaign template loading and management.

Templates define stage configurations and prompts for specific campaign types.
"""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class StageConfig(BaseModel):
    """Configuration for a single stage."""

    agent: str
    exit_criteria: dict[str, Any] = Field(default_factory=dict)
    prompt_file: str | None = None


class TemplateConfig(BaseModel):
    """Complete template configuration."""

    name: str
    description: str
    stages: dict[str, StageConfig]


class Template:
    """Campaign template with prompts."""

    def __init__(self, config: TemplateConfig, template_dir: Path):
        self.config = config
        self.template_dir = template_dir
        self._prompts: dict[str, str] = {}

    @property
    def name(self) -> str:
        return self.config.name

    @property
    def description(self) -> str:
        return self.config.description

    @property
    def stages(self) -> dict[str, StageConfig]:
        return self.config.stages

    def get_prompt(self, stage: str) -> str | None:
        """Get the prompt for a stage.

        Args:
            stage: Stage name

        Returns:
            Prompt content if found, None otherwise
        """
        if stage in self._prompts:
            return self._prompts[stage]

        prompt_path = self.template_dir / "prompts" / f"{stage}.md"
        if prompt_path.exists():
            content = prompt_path.read_text()
            self._prompts[stage] = content
            return content

        return None

    def get_exit_criteria(self, stage: str) -> dict[str, Any]:
        """Get exit criteria for a stage.

        Args:
            stage: Stage name

        Returns:
            Exit criteria dict
        """
        stage_config = self.stages.get(stage)
        if stage_config:
            return stage_config.exit_criteria
        return {}


class TemplateNotFoundError(Exception):
    """Template not found."""

    def __init__(self, name: str, searched_paths: list[Path]):
        self.name = name
        self.searched_paths = searched_paths
        paths_str = "\n".join(f"  - {p}" for p in searched_paths)
        super().__init__(f"Template '{name}' not found in:\n{paths_str}")


def load_template(
    name: str,
    search_paths: list[Path] | None = None,
) -> Template:
    """Load a template by name.

    Args:
        name: Template name (e.g., "product-launch")
        search_paths: Directories to search for templates

    Returns:
        Loaded Template

    Raises:
        TemplateNotFoundError: If template not found
    """
    if search_paths is None:
        search_paths = [
            Path(__file__).parent.parent / "templates",  # Package templates
            Path("~/.agentcy/templates").expanduser(),   # User templates
            Path("./templates"),                         # Local templates
        ]

    for base_path in search_paths:
        template_dir = base_path / name
        config_path = template_dir / "config.yaml"

        if config_path.exists():
            with open(config_path) as f:
                data = yaml.safe_load(f)

            # Parse stages
            stages = {}
            for stage_name, stage_data in data.get("stages", {}).items():
                # Handle exit_criteria as list or dict
                raw_criteria = stage_data.get("exit_criteria", {})
                if isinstance(raw_criteria, list):
                    # Convert list of dicts to single dict
                    exit_criteria = {}
                    for item in raw_criteria:
                        if isinstance(item, dict):
                            exit_criteria.update(item)
                else:
                    exit_criteria = raw_criteria

                stages[stage_name] = StageConfig(
                    agent=stage_data.get("agent", stage_name),
                    exit_criteria=exit_criteria,
                    prompt_file=stage_data.get("prompt_file"),
                )

            config = TemplateConfig(
                name=data.get("name", name),
                description=data.get("description", ""),
                stages=stages,
            )

            return Template(config, template_dir)

    raise TemplateNotFoundError(name, search_paths)


def list_templates(
    search_paths: list[Path] | None = None,
) -> list[dict[str, str]]:
    """List available templates.

    Args:
        search_paths: Directories to search

    Returns:
        List of template info dicts
    """
    if search_paths is None:
        search_paths = [
            Path(__file__).parent.parent / "templates",
            Path("~/.agentcy/templates").expanduser(),
            Path("./templates"),
        ]

    templates = []
    seen = set()

    for base_path in search_paths:
        if not base_path.exists():
            continue

        for item in base_path.iterdir():
            if item.is_dir() and item.name not in seen:
                config_path = item / "config.yaml"
                if config_path.exists():
                    try:
                        with open(config_path) as f:
                            data = yaml.safe_load(f)
                        templates.append({
                            "name": data.get("name", item.name),
                            "description": data.get("description", ""),
                            "path": str(item),
                        })
                        seen.add(item.name)
                    except Exception:
                        pass

    return templates
