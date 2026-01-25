"""Rich display components for CLI.

Provides:
- Campaign header with branding
- Stage progress with spinner
- Cost summary display
- Artifact previews
"""

from typing import Any

from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table
from rich.text import Text
from rich.tree import Tree

from agentcy.models.campaign import Campaign
from agentcy.models.stages import STAGE_ORDER, Stage

console = Console()


def display_header(campaign: Campaign, brand_name: str | None = None) -> None:
    """Display campaign header.

    Args:
        campaign: Campaign object
        brand_name: Optional brand name
    """
    title = Text()
    title.append("AGENTCY", style="bold cyan")
    title.append(" | ", style="dim")
    title.append(campaign.template, style="yellow")

    subtitle = Text()
    subtitle.append("Campaign: ", style="dim")
    subtitle.append(campaign.id, style="bold")
    if brand_name:
        subtitle.append(" | Brand: ", style="dim")
        subtitle.append(brand_name, style="green")

    panel = Panel(
        Group(title, subtitle),
        border_style="cyan",
        padding=(0, 2),
    )
    console.print(panel)
    console.print()


def display_brief(brief: str) -> None:
    """Display the campaign brief.

    Args:
        brief: Campaign brief text
    """
    console.print(Panel(brief, title="Brief", border_style="dim"))
    console.print()


def create_stage_progress() -> Progress:
    """Create a Rich Progress for stage execution.

    Returns:
        Configured Progress object
    """
    return Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(bar_width=30),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=console,
    )


def display_stage_tree(current: Stage, results: dict[str, Any]) -> None:
    """Display stage progress as a tree.

    Args:
        current: Current stage
        results: Stage results dict
    """
    tree = Tree("[bold]Campaign Progress")

    for stage in STAGE_ORDER:
        if stage == Stage.INTAKE:
            continue  # Skip intake in display

        result = results.get(stage.value)

        if stage == current:
            icon = "▶"
            style = "bold yellow"
            status = "running"
        elif result and result.approved:
            icon = "✓"
            style = "green"
            status = "complete"
        elif result:
            icon = "○"
            style = "dim yellow"
            status = "pending approval"
        else:
            icon = "○"
            style = "dim"
            status = "pending"

        tree.add(f"[{style}]{icon} {stage.value.upper()}[/] [{style}]{status}[/]")

    console.print(tree)
    console.print()


def display_cost_summary(
    total_tokens: int,
    total_cost: float,
    by_stage: dict[str, dict[str, Any]] | None = None,
) -> None:
    """Display cost summary.

    Args:
        total_tokens: Total tokens used
        total_cost: Total cost in USD
        by_stage: Optional breakdown by stage
    """
    table = Table(title="Cost Summary", box=None)
    table.add_column("Metric", style="dim")
    table.add_column("Value", justify="right")

    table.add_row("Total Tokens", f"{total_tokens:,}")
    table.add_row("Estimated Cost", f"${total_cost:.4f}")

    if by_stage:
        table.add_row("", "")
        table.add_row("[bold]By Stage", "")
        for stage, data in by_stage.items():
            table.add_row(
                f"  {stage}",
                f"{data.get('tokens', 0):,} (${data.get('cost_usd', 0):.4f})",
            )

    console.print(table)
    console.print()


def display_completion(
    campaign: Campaign,
    output_path: str,
    duration_seconds: float | None = None,
) -> None:
    """Display campaign completion summary.

    Args:
        campaign: Completed campaign
        output_path: Path to output directory
        duration_seconds: Optional total duration
    """
    console.print()

    # Success message
    console.print(
        Panel(
            "[bold green]Campaign Complete![/]",
            border_style="green",
        )
    )
    console.print()

    # Summary table
    table = Table(box=None)
    table.add_column("", style="dim")
    table.add_column("")

    table.add_row("Campaign ID", campaign.id)
    table.add_row("Template", campaign.template)
    if campaign.brand_name:
        table.add_row("Brand", campaign.brand_name)
    table.add_row("Output", output_path)

    if duration_seconds:
        minutes = int(duration_seconds // 60)
        seconds = int(duration_seconds % 60)
        table.add_row("Duration", f"{minutes}m {seconds}s")

    if campaign.total_tokens > 0:
        table.add_row("Tokens Used", f"{campaign.total_tokens:,}")
        table.add_row("Estimated Cost", f"${campaign.total_cost_usd:.4f}")

    console.print(table)
    console.print()


def display_artifact_summary(
    artifact_type: str,
    artifact: dict[str, Any],
) -> None:
    """Display a compact artifact summary.

    Args:
        artifact_type: Type of artifact
        artifact: Artifact data
    """
    table = Table(title=f"{artifact_type.upper()} Summary", box=None)
    table.add_column("Field", style="dim")
    table.add_column("Value")

    if artifact_type == "research":
        table.add_row("Sources", str(len(artifact.get("sources", []))))
        table.add_row("Insights", str(len(artifact.get("insights", []))))
        table.add_row("Competitors", str(len(artifact.get("competitors", []))))

    elif artifact_type == "strategy":
        pos = artifact.get("positioning", "")
        table.add_row("Positioning", pos[:50] + "..." if len(pos) > 50 else pos)
        table.add_row("Pillars", str(len(artifact.get("messaging_pillars", []))))

    elif artifact_type == "creative":
        table.add_row("Headlines", str(len(artifact.get("headline_variants", []))))
        table.add_row("Body Variants", str(len(artifact.get("body_variants", []))))
        table.add_row("CTAs", str(len(artifact.get("cta_variants", []))))
        score = artifact.get("brand_voice_score", 0)
        table.add_row("Brand Score", f"{score:.0%}")

    elif artifact_type == "activation":
        table.add_row("Channels", str(len(artifact.get("channels", []))))
        table.add_row("Calendar", str(len(artifact.get("content_calendar", []))))
        table.add_row("KPIs", str(len(artifact.get("kpis", []))))

    console.print(table)


class StageSpinner:
    """Context manager for stage execution with spinner."""

    def __init__(self, stage: str, description: str | None = None):
        self.stage = stage
        self.description = description or f"Running {stage}..."
        self.progress = create_stage_progress()
        self.task_id = None
        self.live = None

    def __enter__(self) -> "StageSpinner":
        self.live = Live(self.progress, console=console, refresh_per_second=10)
        self.live.__enter__()
        self.task_id = self.progress.add_task(self.description, total=None)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.task_id is not None:
            self.progress.remove_task(self.task_id)
        if self.live:
            self.live.__exit__(exc_type, exc_val, exc_tb)

    def update(self, description: str) -> None:
        """Update spinner description."""
        if self.task_id is not None:
            self.progress.update(self.task_id, description=description)
