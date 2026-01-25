"""CLI for agency - AI marketing campaign generator.

Default: Non-interactive, outputs JSON
--interactive: Enables human approval gates
"""

import json
import sys
import uuid
from pathlib import Path

import typer
from rich.console import Console

from agency.stages import (
    CreativeResult,
    ResearchResult,
    StrategyResult,
    activate,
    creative,
    research,
    strategy,
)

app = typer.Typer(help="AI marketing agency. Non-interactive by default.")
console = Console()

STAGES = ["research", "strategy", "creative", "activation"]


def _output_json(result, output: Path | None) -> None:
    """Output result as JSON to stdout or file."""
    data = result.model_dump_json(indent=2)
    if output:
        output.write_text(data)
        console.print(f"[dim]Saved to {output}[/dim]", file=sys.stderr)
    else:
        print(data)


def _read_stdin_json(schema):
    """Read JSON from stdin and parse into schema."""
    if sys.stdin.isatty():
        raise typer.BadParameter("Expected JSON input from stdin")
    data = json.load(sys.stdin)
    return schema.model_validate(data)


@app.command()
def run(
    brief: str = typer.Argument(..., help="Campaign brief"),
    output: Path = typer.Option(None, "-o", "--output", help="Output file (default: stdout)"),
    interactive: bool = typer.Option(False, "-i", "--interactive", help="Enable human gates"),
) -> None:
    """Run full campaign pipeline.

    Default: Runs all stages, outputs final JSON
    --interactive: Prompts for approval at each stage
    """
    if interactive:
        _run_interactive(brief)
        return

    # Non-interactive: run all stages
    console.print("[dim]Running research...[/dim]", file=sys.stderr)
    r = research(brief)

    console.print("[dim]Running strategy...[/dim]", file=sys.stderr)
    s = strategy(r)

    console.print("[dim]Running creative...[/dim]", file=sys.stderr)
    c = creative(s)

    console.print("[dim]Running activation...[/dim]", file=sys.stderr)
    a = activate(s, c)

    # Combine results
    result = {
        "brief": brief,
        "research": r.model_dump(),
        "strategy": s.model_dump(),
        "creative": c.model_dump(),
        "activation": a.model_dump(),
    }

    data = json.dumps(result, indent=2, default=str)
    if output:
        output.write_text(data)
        console.print(f"[green]Saved to {output}[/green]", file=sys.stderr)
    else:
        print(data)


@app.command("research")
def cmd_research(
    brief: str = typer.Argument(..., help="Research topic or campaign brief"),
    output: Path = typer.Option(None, "-o", "--output", help="Output file"),
) -> None:
    """Run research stage only.

    Example: agency research "AI dev tools market"
    """
    result = research(brief)
    _output_json(result, output)


@app.command("strategy")
def cmd_strategy(
    output: Path = typer.Option(None, "-o", "--output", help="Output file"),
) -> None:
    """Run strategy stage from research input.

    Example: agency research "brief" | agency strategy
    """
    r = _read_stdin_json(ResearchResult)
    result = strategy(r)
    _output_json(result, output)


@app.command("creative")
def cmd_creative(
    output: Path = typer.Option(None, "-o", "--output", help="Output file"),
) -> None:
    """Run creative stage from strategy input.

    Example: agency strategy < research.json | agency creative
    """
    s = _read_stdin_json(StrategyResult)
    result = creative(s)
    _output_json(result, output)


@app.command("activate")
def cmd_activate(
    strategy_file: Path = typer.Option(None, "-s", "--strategy", help="Strategy JSON file"),
    output: Path = typer.Option(None, "-o", "--output", help="Output file"),
) -> None:
    """Run activation stage from creative input.

    Example: agency creative < strategy.json | agency activate -s strategy.json
    """
    c = _read_stdin_json(CreativeResult)

    # Need strategy too - from file or must be piped separately
    if strategy_file:
        if not strategy_file.exists():
            raise typer.BadParameter(f"Strategy file not found: {strategy_file}")
        try:
            s = StrategyResult.model_validate_json(strategy_file.read_text())
        except Exception as e:
            raise typer.BadParameter(f"Invalid strategy JSON: {e}")
    else:
        raise typer.BadParameter(
            "Activation requires strategy. Use -s/--strategy to provide strategy JSON file"
        )

    result = activate(s, c)
    _output_json(result, output)


@app.command("list")
def cmd_list() -> None:
    """List saved campaigns (from --interactive sessions)."""
    from agency.core.store import get_store

    store = get_store()
    campaigns = store.list_all()

    if not campaigns:
        console.print("[dim]No campaigns found[/dim]")
        return

    for c in campaigns:
        console.print(f"[bold]{c.id}[/bold] - {c.stage} - {c.brief[:50]}...")


@app.command("resume")
def cmd_resume(
    campaign_id: str = typer.Argument(..., help="Campaign ID to resume"),
) -> None:
    """Resume an interactive campaign session."""
    from agency.core.store import get_store

    store = get_store()
    campaign = store.get(campaign_id)

    if not campaign:
        console.print(f"[red]Campaign {campaign_id} not found[/red]")
        raise typer.Exit(1)

    _run_interactive(campaign.brief, campaign_id=campaign_id)


def _run_interactive(brief: str, campaign_id: str | None = None) -> None:
    """Run interactive pipeline with human gates."""
    from agency.core.store import get_store
    from agency.ui.prompts import display_progress, prompt_gate

    store = get_store()

    # Create or load campaign
    if campaign_id:
        campaign = store.get(campaign_id)
        if not campaign:
            console.print(f"[red]Campaign {campaign_id} not found[/red]")
            raise typer.Exit(1)
    else:
        campaign_id = str(uuid.uuid4())[:8]
        campaign = store.create(campaign_id, brief)

    console.print(f"[bold]Campaign:[/bold] {campaign_id}")
    console.print(f"[bold]Brief:[/bold] {brief[:100]}...")
    console.print()

    # Stage execution with gates
    current = campaign.stage

    # Research
    if current == "research":
        display_progress("research", STAGES)
        r = research(brief)
        gate = prompt_gate("research", r)

        if gate.should_quit:
            store.save_stage(campaign_id, "research", r, "research")
            console.print(f"[yellow]Saved. Resume with: agency resume {campaign_id}[/yellow]")
            raise typer.Exit(0)

        while gate.should_regenerate:
            console.print("[dim]Regenerating research...[/dim]")
            r = research(brief)
            gate = prompt_gate("research", r)
            if gate.should_quit:
                store.save_stage(campaign_id, "research", r, "research")
                console.print(f"[yellow]Saved. Resume with: agency resume {campaign_id}[/yellow]")
                raise typer.Exit(0)

        if gate.should_continue:
            store.save_stage(campaign_id, "research", r, "strategy")
            current = "strategy"

    # Load previous research if resuming
    r = store.load_stage(campaign_id, "research", ResearchResult)
    if not r:
        console.print("[red]No research found. Start from beginning.[/red]")
        raise typer.Exit(1)

    # Strategy
    if current == "strategy":
        display_progress("strategy", STAGES)
        s = strategy(r)
        gate = prompt_gate("strategy", s)

        if gate.should_quit:
            store.save_stage(campaign_id, "strategy", s, "strategy")
            console.print(f"[yellow]Saved. Resume with: agency resume {campaign_id}[/yellow]")
            raise typer.Exit(0)

        while gate.should_regenerate:
            console.print("[dim]Regenerating strategy...[/dim]")
            s = strategy(r)
            gate = prompt_gate("strategy", s)
            if gate.should_quit:
                store.save_stage(campaign_id, "strategy", s, "strategy")
                console.print(f"[yellow]Saved. Resume with: agency resume {campaign_id}[/yellow]")
                raise typer.Exit(0)

        if gate.should_continue:
            store.save_stage(campaign_id, "strategy", s, "creative")
            current = "creative"

    s = store.load_stage(campaign_id, "strategy", StrategyResult)
    if not s:
        console.print("[red]No strategy found.[/red]")
        raise typer.Exit(1)

    # Creative
    if current == "creative":
        display_progress("creative", STAGES)
        c = creative(s)
        gate = prompt_gate("creative", c)

        if gate.should_quit:
            store.save_stage(campaign_id, "creative", c, "creative")
            console.print(f"[yellow]Saved. Resume with: agency resume {campaign_id}[/yellow]")
            raise typer.Exit(0)

        while gate.should_regenerate:
            console.print("[dim]Regenerating creative...[/dim]")
            c = creative(s)
            gate = prompt_gate("creative", c)
            if gate.should_quit:
                store.save_stage(campaign_id, "creative", c, "creative")
                console.print(f"[yellow]Saved. Resume with: agency resume {campaign_id}[/yellow]")
                raise typer.Exit(0)

        if gate.should_continue:
            store.save_stage(campaign_id, "creative", c, "activation")
            current = "activation"

    c = store.load_stage(campaign_id, "creative", CreativeResult)
    if not c:
        console.print("[red]No creative found.[/red]")
        raise typer.Exit(1)

    # Activation
    if current == "activation":
        display_progress("activation", STAGES)
        a = activate(s, c)
        gate = prompt_gate("activation", a)

        if gate.should_quit:
            store.save_stage(campaign_id, "activation", a, "activation")
            console.print(f"[yellow]Saved. Resume with: agency resume {campaign_id}[/yellow]")
            raise typer.Exit(0)

        while gate.should_regenerate:
            console.print("[dim]Regenerating activation...[/dim]")
            a = activate(s, c)
            gate = prompt_gate("activation", a)
            if gate.should_quit:
                store.save_stage(campaign_id, "activation", a, "activation")
                console.print(f"[yellow]Saved. Resume with: agency resume {campaign_id}[/yellow]")
                raise typer.Exit(0)

        if gate.should_continue:
            store.save_stage(campaign_id, "activation", a, "done")

    console.print("[bold green]Campaign complete![/bold green]")
    console.print(f"Results saved to: .agency/{campaign_id}.json")


if __name__ == "__main__":
    app()
