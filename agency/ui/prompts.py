"""Human-in-the-loop approval gates for --interactive mode.

Actions:
    [A]pprove - Accept and proceed
    [E]dit - Modify result inline (TODO)
    [R]egenerate - Request new version
    [S]kip - Bypass stage
    [Q]uit - Save state and exit
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

console = Console()


class GateAction(str, Enum):
    """User action at approval gate."""
    APPROVE = "approve"
    REGENERATE = "regenerate"
    SKIP = "skip"
    QUIT = "quit"


class GateResult:
    """Result from gate interaction."""

    def __init__(self, action: GateAction, feedback: str | None = None):
        self.action = action
        self.feedback = feedback

    @property
    def should_continue(self) -> bool:
        return self.action in (GateAction.APPROVE, GateAction.SKIP)

    @property
    def should_regenerate(self) -> bool:
        return self.action == GateAction.REGENERATE

    @property
    def should_quit(self) -> bool:
        return self.action == GateAction.QUIT


def display_result(stage: str, result: BaseModel) -> None:
    """Display stage result in rich format."""
    console.print()
    console.print(Panel(f"[bold blue]{stage.upper()}[/bold blue]", border_style="blue"))

    data = result.model_dump()
    md = _format_result(stage, data)
    console.print(Markdown(md))
    console.print()


def _format_result(stage: str, data: dict[str, Any]) -> str:
    """Format result as markdown."""
    lines = []

    if stage == "research":
        if insights := data.get("insights", []):
            lines.append("**Insights:**")
            for i in insights[:5]:
                lines.append(f"- {i}")
        if competitors := data.get("competitors", []):
            lines.append(f"\n**Competitors:** {len(competitors)} analyzed")

    elif stage == "strategy":
        if pos := data.get("positioning"):
            lines.append(f"**Positioning:**\n{pos[:200]}...")
        if pillars := data.get("messaging_pillars", []):
            lines.append("\n**Messaging Pillars:**")
            for p in pillars:
                lines.append(f"- {p}")

    elif stage == "creative":
        if headlines := data.get("headlines", []):
            lines.append("**Headlines:**")
            for h in headlines[:5]:
                lines.append(f"- {h}")
        if tagline := data.get("tagline"):
            lines.append(f"\n**Tagline:** {tagline}")

    elif stage == "activation":
        if channels := data.get("channels", []):
            lines.append("**Channels:**")
            for ch in channels[:4]:
                lines.append(f"- {ch.get('name', 'Unknown')}: {ch.get('objective', '')[:50]}")
        if kpis := data.get("kpis", []):
            lines.append(f"\n**KPIs:** {len(kpis)} defined")

    return "\n".join(lines) if lines else f"```json\n{_pretty_json(data)}\n```"


def _pretty_json(data: dict) -> str:
    """Format dict as pretty JSON."""
    import json
    return json.dumps(data, indent=2, default=str)


def prompt_gate(stage: str, result: BaseModel) -> GateResult:
    """Display gate and get user action.

    Args:
        stage: Current stage name
        result: Stage result to review

    Returns:
        GateResult with action and optional feedback
    """
    display_result(stage, result)

    # Action menu
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_row("[bold green][A]pprove[/]", "Accept and continue")
    table.add_row("[bold cyan][R]egenerate[/]", "Generate new version")
    table.add_row("[bold magenta][S]kip[/]", "Skip this stage")
    table.add_row("[bold red][Q]uit[/]", "Save and exit")
    table.add_row("[bold][F]ull[/]", "Show full JSON")
    console.print(table)
    console.print()

    while True:
        choice = Prompt.ask(
            "[bold]Action[/]",
            choices=["a", "r", "s", "q", "f"],
            default="a",
        ).lower()

        if choice == "a":
            return GateResult(GateAction.APPROVE)

        elif choice == "r":
            feedback = Prompt.ask("[bold]Feedback (optional)[/]", default="")
            return GateResult(GateAction.REGENERATE, feedback=feedback or None)

        elif choice == "s":
            if Prompt.ask("[yellow]Skip?[/]", choices=["y", "n"], default="n") == "y":
                return GateResult(GateAction.SKIP)

        elif choice == "q":
            if Prompt.ask("[yellow]Save and quit?[/]", choices=["y", "n"], default="n") == "y":
                return GateResult(GateAction.QUIT)

        elif choice == "f":
            console.print(Panel(
                Markdown(f"```json\n{_pretty_json(result.model_dump())}\n```"),
                title="Full Result",
                border_style="dim",
            ))
            console.print()


def display_progress(current: str, stages: list[str]) -> None:
    """Display pipeline progress bar."""
    parts = []
    for s in stages:
        if s == current:
            parts.append(f"[bold yellow]> {s} <[/]")
        else:
            parts.append(f"[dim]{s}[/]")
    console.print(" -> ".join(parts))
    console.print()
