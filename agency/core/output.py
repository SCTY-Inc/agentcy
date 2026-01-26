"""Output formatting for CLI.

Supports: json, yaml, markdown, table
"""

import json
from enum import Enum

from pydantic import BaseModel


class OutputFormat(str, Enum):
    """Supported output formats."""

    JSON = "json"
    YAML = "yaml"
    MARKDOWN = "markdown"
    TABLE = "table"


def format_output(result: BaseModel, fmt: OutputFormat) -> str:
    """Format Pydantic model for output.

    Args:
        result: Pydantic model instance
        fmt: Output format

    Returns:
        Formatted string
    """
    if fmt == OutputFormat.JSON:
        return result.model_dump_json(indent=2)

    if fmt == OutputFormat.YAML:
        return _to_yaml(result)

    if fmt == OutputFormat.MARKDOWN:
        return _to_markdown(result)

    if fmt == OutputFormat.TABLE:
        return _to_table(result)

    return result.model_dump_json(indent=2)


def _to_yaml(result: BaseModel) -> str:
    """Convert to YAML format."""
    try:
        import yaml

        return yaml.dump(result.model_dump(), default_flow_style=False, sort_keys=False)
    except ImportError:
        # Fallback to simple YAML-like format
        return _simple_yaml(result.model_dump())


def _simple_yaml(data: dict, indent: int = 0) -> str:
    """Simple YAML-like formatter without pyyaml dependency."""
    lines = []
    prefix = "  " * indent

    for key, value in data.items():
        if isinstance(value, dict):
            lines.append(f"{prefix}{key}:")
            lines.append(_simple_yaml(value, indent + 1))
        elif isinstance(value, list):
            lines.append(f"{prefix}{key}:")
            for item in value:
                if isinstance(item, dict):
                    lines.append(f"{prefix}  -")
                    for k, v in item.items():
                        lines.append(f"{prefix}    {k}: {v}")
                else:
                    lines.append(f"{prefix}  - {item}")
        else:
            lines.append(f"{prefix}{key}: {value}")

    return "\n".join(lines)


def _to_markdown(result: BaseModel) -> str:
    """Convert to Markdown format."""
    lines = []
    data = result.model_dump()
    model_name = result.__class__.__name__

    lines.append(f"# {model_name}")
    lines.append("")

    for key, value in data.items():
        title = key.replace("_", " ").title()

        if isinstance(value, str):
            lines.append(f"## {title}")
            lines.append(value)
            lines.append("")

        elif isinstance(value, list):
            lines.append(f"## {title}")
            for item in value:
                if isinstance(item, dict):
                    # Nested object as sub-section
                    if "name" in item:
                        lines.append(f"### {item['name']}")
                    for k, v in item.items():
                        if k != "name" and v:
                            if isinstance(v, list):
                                lines.append(f"**{k.replace('_', ' ').title()}:**")
                                for i in v:
                                    lines.append(f"- {i}")
                            else:
                                lines.append(f"**{k.replace('_', ' ').title()}:** {v}")
                    lines.append("")
                else:
                    lines.append(f"- {item}")
            lines.append("")

        elif isinstance(value, dict):
            lines.append(f"## {title}")
            if "name" in value:
                lines.append(f"**{value['name']}**")
            for k, v in value.items():
                if k != "name" and v:
                    k_title = k.replace("_", " ").title()
                    if isinstance(v, list):
                        lines.append(f"**{k_title}:**")
                        for i in v:
                            lines.append(f"- {i}")
                    else:
                        lines.append(f"**{k_title}:** {v}")
            lines.append("")

    return "\n".join(lines)


def _to_table(result: BaseModel) -> str:
    """Convert to Rich table format (string representation)."""
    from io import StringIO

    from rich.console import Console
    from rich.table import Table

    data = result.model_dump()
    model_name = result.__class__.__name__

    # Create string buffer
    console = Console(file=StringIO(), force_terminal=True, width=120)

    table = Table(title=model_name, show_header=True, header_style="bold")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="white")

    for key, value in data.items():
        key_display = key.replace("_", " ").title()

        if isinstance(value, list):
            if len(value) == 0:
                value_display = "(empty)"
            elif isinstance(value[0], dict):
                value_display = f"{len(value)} items"
            else:
                value_display = "\n".join(f"• {v}" for v in value[:5])
                if len(value) > 5:
                    value_display += f"\n... +{len(value) - 5} more"
        elif isinstance(value, dict):
            if "name" in value:
                value_display = value["name"]
            else:
                value_display = json.dumps(value, indent=2)[:200]
        else:
            value_display = str(value)[:200]

        table.add_row(key_display, value_display)

    console.print(table)
    return console.file.getvalue()
