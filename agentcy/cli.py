"""Typer CLI entry points for Agentcy.

Commands:
    agentcy init --template <name> --brand <path>
    agentcy run --brief <text> --brand <path> --output <path>
    agentcy resume <campaign-path>
    agentcy export <campaign-path> --format <md|pdf|notion>
"""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

app = typer.Typer(
    name="agentcy",
    help="AI-powered marketing campaign generator with human approval gates",
    no_args_is_help=True,
)
console = Console()


@app.command()
def init(
    template: str = typer.Option("product-launch", help="Campaign template"),
    brand: Optional[Path] = typer.Option(None, help="Path to brand kit directory"),
    output: Path = typer.Option(Path("./campaigns"), help="Output directory"),
) -> None:
    """Initialize a new campaign project."""
    console.print(f"[bold]Initializing campaign with template:[/] {template}")
    # TODO: Implement init logic
    raise typer.Exit(code=1)


@app.command()
def run(
    brief: str = typer.Option(..., help="Campaign brief text"),
    brand: Optional[Path] = typer.Option(None, help="Path to brand kit directory"),
    output: Path = typer.Option(Path("./campaigns"), help="Output directory"),
    template: str = typer.Option("product-launch", help="Campaign template"),
) -> None:
    """Run a campaign from brief to completion."""
    console.print(f"[bold]Running campaign:[/] {brief[:50]}...")
    # TODO: Implement run logic
    raise typer.Exit(code=1)


@app.command()
def resume(
    campaign_path: Path = typer.Argument(..., help="Path to campaign directory"),
) -> None:
    """Resume a paused campaign."""
    console.print(f"[bold]Resuming campaign:[/] {campaign_path}")
    # TODO: Implement resume logic
    raise typer.Exit(code=1)


@app.command()
def export(
    campaign_path: Path = typer.Argument(..., help="Path to campaign directory"),
    format: str = typer.Option("md", help="Export format (md, pdf, notion)"),
) -> None:
    """Export campaign to specified format."""
    console.print(f"[bold]Exporting campaign:[/] {campaign_path} as {format}")
    # TODO: Implement export logic
    raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
