"""Configuration loading from YAML files.

Loads:
    ~/.agentcy/config.yaml - global defaults
    brand/brand.yaml - brand kit
    apis.yaml - external API credentials
"""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, ValidationError

from agentcy.models.brand import BrandKit


class ModelConfig(BaseModel):
    """Model configuration per task type."""

    default: str = "gemini-3-flash-preview"
    research: str = "gemini-2.5-flash-lite"
    creative: str = "gemini-3-flash-preview"
    critic: str = "gemini-3-flash-preview"


class AgentcyConfig(BaseModel):
    """Global Agentcy configuration."""

    models: ModelConfig = Field(default_factory=ModelConfig)
    templates_dir: Path = Field(default=Path("~/.agentcy/templates").expanduser())
    output_dir: Path = Field(default=Path("./campaigns"))


class ConfigError(Exception):
    """Configuration loading error with helpful message."""

    pass


def load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML file, raising ConfigError on failure."""
    if not path.exists():
        raise ConfigError(f"Config file not found: {path}")

    try:
        with open(path) as f:
            data = yaml.safe_load(f)
            return data if data else {}
    except yaml.YAMLError as e:
        raise ConfigError(f"Invalid YAML in {path}: {e}")


def load_config(config_path: Path | None = None) -> AgentcyConfig:
    """Load global Agentcy configuration.

    Args:
        config_path: Path to config.yaml. Defaults to ~/.agentcy/config.yaml

    Returns:
        AgentcyConfig with merged defaults and file values
    """
    if config_path is None:
        config_path = Path("~/.agentcy/config.yaml").expanduser()

    if not config_path.exists():
        # Return defaults if no config file
        return AgentcyConfig()

    try:
        data = load_yaml(config_path)
        return AgentcyConfig(**data)
    except ValidationError as e:
        errors = e.errors()
        msg = f"Invalid config in {config_path}:\n"
        for err in errors:
            loc = ".".join(str(x) for x in err["loc"])
            msg += f"  - {loc}: {err['msg']}\n"
        raise ConfigError(msg)


def load_brand(brand_path: Path) -> BrandKit:
    """Load brand kit from YAML file.

    Args:
        brand_path: Path to brand.yaml or directory containing it

    Returns:
        BrandKit with validated brand configuration

    Raises:
        ConfigError: If file not found or validation fails
    """
    # Handle both file and directory paths
    if brand_path.is_dir():
        brand_path = brand_path / "brand.yaml"

    if not brand_path.exists():
        raise ConfigError(
            f"Brand file not found: {brand_path}\n"
            f"Expected a brand.yaml file with at minimum:\n"
            f"  name: Your Brand Name"
        )

    try:
        data = load_yaml(brand_path)
        return BrandKit(**data)
    except ValidationError as e:
        errors = e.errors()
        msg = f"Invalid brand config in {brand_path}:\n"
        for err in errors:
            loc = ".".join(str(x) for x in err["loc"])
            msg += f"  - {loc}: {err['msg']}\n"
        raise ConfigError(msg)


def load_voice_examples(brand: BrandKit, brand_dir: Path) -> str | None:
    """Load voice examples file if specified in brand kit.

    Args:
        brand: Loaded brand kit
        brand_dir: Directory containing brand files

    Returns:
        Contents of voice examples file, or None if not specified
    """
    if not brand.voice.examples_file:
        return None

    examples_path = brand_dir / brand.voice.examples_file
    if not examples_path.exists():
        return None

    return examples_path.read_text()
