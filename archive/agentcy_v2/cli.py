"""Typer CLI entry points for Agentcy.

Commands:
    agentcy init --template <name> --brand <path>
    agentcy run --brief <text> --brand <path> --output <path>
    agentcy resume <campaign-id>
    agentcy list
    agentcy export <campaign-path> --format <md|pdf|notion>
"""

from dotenv import load_dotenv

# Load .env before anything else
load_dotenv()

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from agentcy.config import ConfigError, load_brand, load_config
from agentcy.controller import CampaignController, StageExecutionError
from agentcy.gates import (
    GateAction,
    GateResult,
    display_error,
    display_progress,
    prompt_gate,
)
from agentcy.models.campaign import Campaign
from agentcy.models.stages import Stage
from agentcy.persistence import (
    CampaignStore,
    generate_campaign_id,
    get_campaign_layout,
)

app = typer.Typer(
    name="agentcy",
    help="AI-powered marketing campaign generator with human approval gates",
    no_args_is_help=True,
)
console = Console()


def _run_campaign_loop(
    controller: CampaignController,
    store: CampaignStore,
    max_retries: int = 3,
    auto_approve: bool = False,
) -> None:
    """Main campaign execution loop with gates and retries.

    Args:
        controller: Campaign controller
        store: Persistence store
        max_retries: Max retries per stage on failure
        auto_approve: Skip gates and auto-approve all stages
    """
    campaign = controller.campaign

    # Advance from INTAKE to first real stage
    if campaign.current_stage == Stage.INTAKE:
        controller.advance()
        store.save(campaign)

    while not controller.is_complete:
        current = controller.current_stage

        # Skip DONE stage
        if current == Stage.DONE:
            break

        # Show progress
        completed = [
            Stage(name)
            for name, result in campaign.results.items()
            if result.approved
        ]
        display_progress(current, completed)

        # Run stage with retries
        retries = 0
        artifact = None

        while retries < max_retries:
            try:
                console.print(f"[bold blue]Running {current.value}...[/]")
                artifact = controller.run_stage(current, {})
                break
            except StageExecutionError as e:
                retries += 1
                display_error(current, e)
                if retries < max_retries and e.retryable:
                    console.print(
                        f"[yellow]Retrying ({retries}/{max_retries})...[/]"
                    )
                else:
                    console.print("[red]Stage failed after max retries[/]")
                    store.save(campaign)
                    raise typer.Exit(code=1)

        if artifact is None:
            console.print("[red]No artifact produced[/]")
            raise typer.Exit(code=1)

        # Human gate (skip if auto-approve)
        if auto_approve:
            console.print(f"[green]Auto-approving {current.value}[/]")
            gate_result = GateResult(GateAction.APPROVE)
        else:
            gate_result = prompt_gate(current, artifact)

        if gate_result.action == GateAction.APPROVE:
            controller.approve_stage(current)
            controller.advance()
            store.save(campaign)

        elif gate_result.action == GateAction.EDIT:
            if gate_result.modified_artifact:
                controller.record_result(
                    current, gate_result.modified_artifact, approved=True
                )
                controller.advance()
                store.save(campaign)

        elif gate_result.action == GateAction.REGENERATE:
            # Clear result and retry (next loop iteration)
            console.print(
                f"[cyan]Regenerating {current.value}...[/]"
            )
            if gate_result.feedback:
                console.print(f"[dim]Feedback: {gate_result.feedback}[/]")
            # Don't save - will regenerate on next iteration

        elif gate_result.action == GateAction.SKIP:
            # Mark as approved but skip
            controller.approve_stage(current)
            controller.advance()
            store.save(campaign)

        elif gate_result.action == GateAction.QUIT:
            console.print("[yellow]Saving and exiting...[/]")
            store.save(campaign)
            console.print(f"[green]Campaign saved: {campaign.id}[/]")
            console.print(f"Resume with: agentcy resume {campaign.id}")
            raise typer.Exit(code=0)

    # Campaign complete
    console.print()
    console.print("[bold green]Campaign complete![/]")
    console.print(f"Campaign ID: {campaign.id}")
    console.print(f"Output: {controller.config.output_dir / campaign.id}")


@app.command()
def init(
    template: str = typer.Option("product-launch", help="Campaign template"),
    brand: Path | None = typer.Option(None, help="Path to brand kit directory"),
    output: Path = typer.Option(Path("./campaigns"), help="Output directory"),
) -> None:
    """Initialize a new campaign project."""
    console.print(f"[bold]Initializing campaign with template:[/] {template}")

    # Create output directory
    output.mkdir(parents=True, exist_ok=True)

    # Generate campaign ID
    campaign_id = generate_campaign_id()

    # Create campaign layout
    layout = get_campaign_layout(output, campaign_id)

    console.print(f"[green]Created campaign directory:[/] {layout.root}")
    console.print(f"Run campaign with: agentcy run --brief 'Your brief' --output {output}")


@app.command()
def run(
    brief: str = typer.Option(..., help="Campaign brief text"),
    brand: Path | None = typer.Option(None, help="Path to brand kit directory"),
    output: Path = typer.Option(Path("./campaigns"), help="Output directory"),
    template: str = typer.Option("product-launch", help="Campaign template"),
    db: Path = typer.Option(Path("agentcy.db"), help="Database file"),
    auto: bool = typer.Option(False, "--auto", help="Auto-approve all stages (no gates)"),
) -> None:
    """Run a campaign from brief to completion."""
    console.print(f"[bold]Starting campaign:[/] {brief[:50]}...")

    # Load config
    try:
        config = load_config()
        config.output_dir = output
    except ConfigError as e:
        console.print(f"[red]Config error:[/] {e}")
        raise typer.Exit(code=1)

    # Load brand kit if provided
    brand_kit = None
    if brand:
        try:
            brand_kit = load_brand(brand)
            console.print(f"[green]Loaded brand:[/] {brand_kit.name}")
        except ConfigError as e:
            console.print(f"[red]Brand error:[/] {e}")
            raise typer.Exit(code=1)

    # Create campaign
    campaign_id = generate_campaign_id()
    campaign = Campaign(
        id=campaign_id,
        brief=brief,
        brand_name=brand_kit.name if brand_kit else None,
        template=template,
    )

    # Initialize store and save
    store = CampaignStore(db)
    store.save(campaign)

    console.print(f"[green]Created campaign:[/] {campaign_id}")

    # Create controller and run
    controller = CampaignController(
        campaign=campaign,
        brand=brand_kit,
        config=config,
    )

    _run_campaign_loop(controller, store, auto_approve=auto)


@app.command()
def resume(
    campaign_id: str = typer.Argument(..., help="Campaign ID to resume"),
    db: Path = typer.Option(Path("agentcy.db"), help="Database file"),
) -> None:
    """Resume a paused campaign."""
    console.print(f"[bold]Resuming campaign:[/] {campaign_id}")

    # Load campaign from database
    store = CampaignStore(db)
    campaign = store.load(campaign_id)

    if not campaign:
        console.print(f"[red]Campaign not found:[/] {campaign_id}")
        console.print("Use 'agentcy list' to see available campaigns")
        raise typer.Exit(code=1)

    if campaign.current_stage == Stage.DONE:
        console.print("[yellow]Campaign already complete[/]")
        raise typer.Exit(code=0)

    console.print(f"[green]Loaded campaign at stage:[/] {campaign.current_stage.value}")

    # Load config
    config = load_config()

    # Load brand kit if available
    brand_kit = None
    if campaign.brand_name:
        console.print(f"[dim]Brand: {campaign.brand_name}[/]")
        # Note: Would need to store brand path to reload

    # Create controller and continue
    controller = CampaignController(
        campaign=campaign,
        brand=brand_kit,
        config=config,
    )

    _run_campaign_loop(controller, store)


@app.command(name="list")
def list_campaigns(
    db: Path = typer.Option(Path("agentcy.db"), help="Database file"),
    all: bool = typer.Option(False, "--all", help="Include completed campaigns"),
) -> None:
    """List campaigns."""
    store = CampaignStore(db)
    campaigns = store.list_campaigns(include_done=all)

    if not campaigns:
        console.print("[dim]No campaigns found[/]")
        return

    table = Table(title="Campaigns")
    table.add_column("ID", style="cyan")
    table.add_column("Brief")
    table.add_column("Stage", style="yellow")
    table.add_column("Updated")

    for c in campaigns:
        table.add_row(c["id"], c["brief"], c["stage"], c["updated"][:19])

    console.print(table)


@app.command()
def export(
    campaign_path: Path = typer.Argument(..., help="Path to campaign directory"),
    format: str = typer.Option("md", help="Export format (md, pdf, notion)"),
) -> None:
    """Export campaign to specified format."""
    console.print(f"[bold]Exporting campaign:[/] {campaign_path} as {format}")

    if format not in ("md", "pdf", "notion"):
        console.print(f"[red]Unsupported format:[/] {format}")
        console.print("Supported: md, pdf, notion")
        raise typer.Exit(code=1)

    if format == "md":
        console.print("[green]Markdown export already in campaign directory[/]")
    elif format == "pdf":
        console.print("[yellow]PDF export coming soon[/]")
    elif format == "notion":
        console.print("[yellow]Notion export coming soon[/]")


if __name__ == "__main__":
    app()
