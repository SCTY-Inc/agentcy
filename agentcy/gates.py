"""Human-in-the-loop approval gates.

CLI prompts for:
    [A]pprove - accept artifact and proceed
    [E]dit - modify artifact inline
    [R]egenerate - request new version
    [S]kip - bypass this stage
    [Q]uit - save state and exit
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from agentcy.models.stages import Stage

console = Console()


class GateAction(str, Enum):
    """User action at a gate."""

    APPROVE = "approve"
    EDIT = "edit"
    REGENERATE = "regenerate"
    SKIP = "skip"
    QUIT = "quit"


class GateResult:
    """Result of a gate interaction."""

    def __init__(
        self,
        action: GateAction,
        modified_artifact: dict[str, Any] | None = None,
        feedback: str | None = None,
    ):
        self.action = action
        self.modified_artifact = modified_artifact
        self.feedback = feedback  # User feedback for regeneration

    @property
    def should_continue(self) -> bool:
        """Whether to continue to next stage."""
        return self.action in (GateAction.APPROVE, GateAction.SKIP)

    @property
    def should_regenerate(self) -> bool:
        """Whether to regenerate current stage."""
        return self.action == GateAction.REGENERATE

    @property
    def should_quit(self) -> bool:
        """Whether to save and exit."""
        return self.action == GateAction.QUIT


def format_artifact_preview(stage: Stage, artifact: dict[str, Any]) -> str:
    """Format artifact for display in gate prompt.

    Args:
        stage: Current stage
        artifact: Artifact data

    Returns:
        Markdown-formatted preview
    """
    if stage == Stage.RESEARCH:
        lines = ["## Research Report"]
        insights = artifact.get("insights", [])
        if insights:
            lines.append("\n**Key Insights:**")
            for i, insight in enumerate(insights[:5], 1):
                lines.append(f"{i}. {insight}")
            if len(insights) > 5:
                lines.append(f"... and {len(insights) - 5} more")
        sources = artifact.get("sources", [])
        if sources:
            lines.append(f"\n**Sources:** {len(sources)} found")
        return "\n".join(lines)

    elif stage == Stage.STRATEGY:
        lines = ["## Strategy Brief"]
        lines.append(f"\n**Positioning:**\n{artifact.get('positioning', 'N/A')}")
        pillars = artifact.get("messaging_pillars", [])
        if pillars:
            lines.append("\n**Messaging Pillars:**")
            for p in pillars:
                lines.append(f"- {p}")
        return "\n".join(lines)

    elif stage == Stage.CREATIVE:
        lines = ["## Copy Deck"]
        headlines = artifact.get("headline_variants", [])
        if headlines:
            lines.append("\n**Headlines:**")
            for h in headlines[:3]:
                lines.append(f"- {h}")
        ctas = artifact.get("cta_variants", [])
        if ctas:
            lines.append("\n**CTAs:**")
            for c in ctas[:3]:
                lines.append(f"- {c}")
        score = artifact.get("brand_voice_score", 0)
        lines.append(f"\n**Brand Voice Score:** {score:.0%}")
        return "\n".join(lines)

    elif stage == Stage.ACTIVATION:
        lines = ["## Activation Plan"]
        channels = artifact.get("channels", [])
        if channels:
            lines.append(f"\n**Channels:** {len(channels)}")
            for ch in channels[:3]:
                lines.append(f"- {ch.get('channel', 'Unknown')}: {ch.get('objective', '')}")
        kpis = artifact.get("kpis", [])
        if kpis:
            lines.append(f"\n**KPIs:** {len(kpis)} defined")
        return "\n".join(lines)

    elif stage == Stage.PACKAGING:
        lines = ["## Package Complete"]
        files = artifact.get("files", {})
        if files:
            lines.append("\n**Exported Files:**")
            for name, path in files.items():
                lines.append(f"- {name}: {path}")
        return "\n".join(lines)

    else:
        return f"## {stage.value.title()}\n\n{artifact}"


def prompt_gate(
    stage: Stage,
    artifact: dict[str, Any] | BaseModel,
    show_full: bool = False,
) -> GateResult:
    """Display gate prompt and get user action.

    Args:
        stage: Current stage
        artifact: Stage output to review
        show_full: Show full artifact instead of preview

    Returns:
        GateResult with user action
    """
    if isinstance(artifact, BaseModel):
        artifact_dict = artifact.model_dump()
    else:
        artifact_dict = artifact

    # Display stage header
    console.print()
    console.print(
        Panel(
            f"[bold blue]Stage: {stage.value.upper()}[/bold blue]",
            border_style="blue",
        )
    )

    # Display artifact preview or full content
    preview = format_artifact_preview(stage, artifact_dict)
    console.print(Markdown(preview))
    console.print()

    # Action menu
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_row("[bold green][A]pprove[/]", "Accept and continue")
    table.add_row("[bold yellow][E]dit[/]", "Modify artifact")
    table.add_row("[bold cyan][R]egenerate[/]", "Generate new version")
    table.add_row("[bold magenta][S]kip[/]", "Skip this stage")
    table.add_row("[bold red][Q]uit[/]", "Save and exit")
    if not show_full:
        table.add_row("[bold][F]ull[/]", "Show full artifact")
    console.print(table)
    console.print()

    # Get action
    while True:
        choice = Prompt.ask(
            "[bold]Action[/]",
            choices=["a", "e", "r", "s", "q", "f"],
            default="a",
        ).lower()

        if choice == "a":
            return GateResult(GateAction.APPROVE)

        elif choice == "e":
            return _handle_edit(stage, artifact_dict)

        elif choice == "r":
            feedback = Prompt.ask(
                "[bold]Feedback for regeneration (optional)[/]",
                default="",
            )
            return GateResult(GateAction.REGENERATE, feedback=feedback or None)

        elif choice == "s":
            confirm = Prompt.ask(
                "[yellow]Skip this stage? (y/n)[/]",
                choices=["y", "n"],
                default="n",
            )
            if confirm == "y":
                return GateResult(GateAction.SKIP)

        elif choice == "q":
            confirm = Prompt.ask(
                "[yellow]Save and quit? (y/n)[/]",
                choices=["y", "n"],
                default="n",
            )
            if confirm == "y":
                return GateResult(GateAction.QUIT)

        elif choice == "f" and not show_full:
            # Recursively show full artifact
            console.print()
            console.print(
                Panel(
                    Markdown(f"```json\n{_format_json(artifact_dict)}\n```"),
                    title="Full Artifact",
                    border_style="dim",
                )
            )
            console.print()


def _handle_edit(stage: Stage, artifact: dict[str, Any]) -> GateResult:
    """Handle edit action for different artifact types.

    Args:
        stage: Current stage
        artifact: Artifact to edit

    Returns:
        GateResult with modified artifact
    """
    console.print("\n[bold]Editing artifact...[/]")
    console.print("[dim]Enter new values (press Enter to keep current)[/]\n")

    modified = artifact.copy()

    if stage == Stage.RESEARCH:
        modified = _edit_research(modified)
    elif stage == Stage.STRATEGY:
        modified = _edit_strategy(modified)
    elif stage == Stage.CREATIVE:
        modified = _edit_creative(modified)
    elif stage == Stage.ACTIVATION:
        modified = _edit_activation(modified)
    else:
        console.print("[yellow]Edit not supported for this stage[/]")
        return GateResult(GateAction.APPROVE)

    return GateResult(GateAction.EDIT, modified_artifact=modified)


def _edit_research(artifact: dict[str, Any]) -> dict[str, Any]:
    """Edit research artifact."""
    # Edit insights
    insights = artifact.get("insights", [])
    console.print(f"[bold]Insights[/] ({len(insights)} current):")
    for i, insight in enumerate(insights, 1):
        console.print(f"  {i}. {insight[:60]}...")

    action = Prompt.ask(
        "Add/remove insights",
        choices=["add", "remove", "skip"],
        default="skip",
    )

    if action == "add":
        new_insight = Prompt.ask("New insight")
        if new_insight:
            artifact["insights"] = insights + [new_insight]
    elif action == "remove":
        idx = Prompt.ask("Remove which number", default="")
        if idx.isdigit() and 1 <= int(idx) <= len(insights):
            del artifact["insights"][int(idx) - 1]

    return artifact


def _edit_strategy(artifact: dict[str, Any]) -> dict[str, Any]:
    """Edit strategy artifact."""
    # Edit positioning
    current_pos = artifact.get("positioning", "")
    console.print(f"[bold]Current positioning:[/]\n{current_pos[:200]}...")
    new_pos = Prompt.ask("New positioning (Enter to keep)", default="")
    if new_pos:
        artifact["positioning"] = new_pos

    # Edit messaging pillars
    pillars = artifact.get("messaging_pillars", [])
    console.print(f"\n[bold]Messaging pillars[/] ({len(pillars)}):")
    for i, p in enumerate(pillars, 1):
        console.print(f"  {i}. {p}")

    action = Prompt.ask(
        "Add/remove/skip",
        choices=["add", "remove", "skip"],
        default="skip",
    )
    if action == "add":
        new_pillar = Prompt.ask("New pillar")
        if new_pillar:
            artifact["messaging_pillars"] = pillars + [new_pillar]
    elif action == "remove":
        idx = Prompt.ask("Remove which number", default="")
        if idx.isdigit() and 1 <= int(idx) <= len(pillars):
            del artifact["messaging_pillars"][int(idx) - 1]

    return artifact


def _edit_creative(artifact: dict[str, Any]) -> dict[str, Any]:
    """Edit creative artifact."""
    # Edit headlines
    headlines = artifact.get("headline_variants", [])
    console.print(f"[bold]Headlines[/] ({len(headlines)}):")
    for i, h in enumerate(headlines, 1):
        console.print(f"  {i}. {h}")

    action = Prompt.ask(
        "Add/edit/remove headline",
        choices=["add", "edit", "remove", "skip"],
        default="skip",
    )
    if action == "add":
        new_headline = Prompt.ask("New headline")
        if new_headline:
            artifact["headline_variants"] = headlines + [new_headline]
    elif action == "edit":
        idx = Prompt.ask("Edit which number", default="1")
        if idx.isdigit() and 1 <= int(idx) <= len(headlines):
            new_text = Prompt.ask("New text", default=headlines[int(idx) - 1])
            artifact["headline_variants"][int(idx) - 1] = new_text
    elif action == "remove":
        idx = Prompt.ask("Remove which number", default="")
        if idx.isdigit() and 1 <= int(idx) <= len(headlines):
            del artifact["headline_variants"][int(idx) - 1]

    return artifact


def _edit_activation(artifact: dict[str, Any]) -> dict[str, Any]:
    """Edit activation artifact."""
    channels = artifact.get("channels", [])
    console.print(f"[bold]Channels[/] ({len(channels)}):")
    for i, ch in enumerate(channels, 1):
        console.print(f"  {i}. {ch.get('channel', 'Unknown')}")

    # For now, just allow removing channels
    action = Prompt.ask(
        "Remove channel or skip",
        choices=["remove", "skip"],
        default="skip",
    )
    if action == "remove":
        idx = Prompt.ask("Remove which number", default="")
        if idx.isdigit() and 1 <= int(idx) <= len(channels):
            del artifact["channels"][int(idx) - 1]

    return artifact


def _format_json(data: dict[str, Any]) -> str:
    """Format dict as pretty JSON."""
    import json

    return json.dumps(data, indent=2, default=str)


def display_progress(current: Stage, completed: list[Stage]) -> None:
    """Display campaign progress bar.

    Args:
        current: Current stage
        completed: List of completed stages
    """
    from agentcy.models.stages import STAGE_ORDER

    console.print()
    progress_parts = []

    for stage in STAGE_ORDER:
        if stage in completed:
            progress_parts.append(f"[green]{stage.value}[/]")
        elif stage == current:
            progress_parts.append(f"[bold yellow]> {stage.value} <[/]")
        else:
            progress_parts.append(f"[dim]{stage.value}[/]")

    console.print(" → ".join(progress_parts))
    console.print()


def display_error(stage: Stage, error: Exception) -> None:
    """Display error message with retry option.

    Args:
        stage: Stage that failed
        error: Exception that occurred
    """
    console.print()
    console.print(
        Panel(
            f"[bold red]Error in {stage.value}[/bold red]\n\n{str(error)}",
            border_style="red",
            title="Stage Failed",
        )
    )


def confirm_quit() -> bool:
    """Confirm quit action.

    Returns:
        True if user confirms quit
    """
    return (
        Prompt.ask(
            "\n[yellow]Save progress and exit?[/]",
            choices=["y", "n"],
            default="n",
        )
        == "y"
    )
