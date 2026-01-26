"""Plugin system for extensible domains.

Plugins are discovered from:
1. Built-in plugins in agency/plugins/
2. Entry points: agency.plugins
3. AGENCY_PLUGINS_PATH environment variable

Each plugin must define:
- name: str - unique identifier
- description: str - what this plugin does
- input_schema: type[BaseModel] - expected input
- output_schema: type[BaseModel] - output type
- run(input) -> output - execution function
"""

import importlib
import importlib.metadata
import os
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import BaseModel


@dataclass
class Plugin:
    """Plugin definition."""

    name: str
    description: str
    input_schema: type[BaseModel] | None
    output_schema: type[BaseModel]
    run: Callable[..., BaseModel]


# Global registry
_plugins: dict[str, Plugin] = {}


def register(
    name: str,
    description: str,
    output_schema: type[BaseModel],
    input_schema: type[BaseModel] | None = None,
) -> Callable:
    """Decorator to register a plugin.

    Usage:
        @register("seo", "SEO analysis", SEOResult, ResearchResult)
        def run(research: ResearchResult) -> SEOResult:
            ...
    """

    def decorator(fn: Callable[..., BaseModel]) -> Callable[..., BaseModel]:
        _plugins[name] = Plugin(
            name=name,
            description=description,
            input_schema=input_schema,
            output_schema=output_schema,
            run=fn,
        )
        return fn

    return decorator


def get(name: str) -> Plugin | None:
    """Get plugin by name."""
    _ensure_loaded()
    return _plugins.get(name)


def list_plugins() -> list[Plugin]:
    """List all registered plugins."""
    _ensure_loaded()
    return list(_plugins.values())


def run_plugin(name: str, input_data: Any) -> BaseModel:
    """Run a plugin by name.

    Args:
        name: Plugin name
        input_data: Input data (will be validated against input_schema)

    Returns:
        Plugin output
    """
    plugin = get(name)
    if not plugin:
        raise ValueError(f"Plugin not found: {name}")

    # Validate input if schema defined
    if plugin.input_schema and isinstance(input_data, dict):
        input_data = plugin.input_schema.model_validate(input_data)

    return plugin.run(input_data)


_loaded = False


def _ensure_loaded() -> None:
    """Load plugins from all sources."""
    global _loaded
    if _loaded:
        return

    # 1. Load built-in plugins
    _load_builtin()

    # 2. Load from entry points
    _load_entrypoints()

    # 3. Load from AGENCY_PLUGINS_PATH
    _load_from_path()

    _loaded = True


def _load_builtin() -> None:
    """Load built-in plugins from this package."""
    # Import built-in plugin modules
    builtins = ["seo", "social"]
    for name in builtins:
        try:
            importlib.import_module(f"agency.plugins.{name}")
        except ImportError:
            pass  # Optional plugin not installed


def _load_entrypoints() -> None:
    """Load plugins from entry points."""
    try:
        eps = importlib.metadata.entry_points(group="agency.plugins")
        for ep in eps:
            try:
                ep.load()
            except Exception:
                pass  # Skip failed plugins
    except Exception:
        pass  # No entry points


def _load_from_path() -> None:
    """Load plugins from AGENCY_PLUGINS_PATH."""
    plugins_path = os.getenv("AGENCY_PLUGINS_PATH")
    if not plugins_path:
        return

    for path_str in plugins_path.split(":"):
        path = Path(path_str)
        if not path.is_dir():
            continue

        for py_file in path.glob("*.py"):
            if py_file.name.startswith("_"):
                continue
            try:
                spec = importlib.util.spec_from_file_location(py_file.stem, py_file)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
            except Exception:
                pass  # Skip failed plugins
