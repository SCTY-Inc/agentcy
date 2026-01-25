"""Campaign export to various formats.

Supports:
- Markdown (default)
- PDF (future)
- Notion (future)
"""

from datetime import datetime
from pathlib import Path
from typing import Any

from agentcy.models.campaign import Campaign
from agentcy.persistence.layout import CampaignLayout


def export_markdown(
    campaign: Campaign,
    output_dir: Path,
) -> dict[str, Path]:
    """Export campaign artifacts to markdown files.

    Args:
        campaign: Campaign with results
        output_dir: Output directory

    Returns:
        Dict mapping artifact names to file paths
    """
    layout = CampaignLayout(output_dir)
    exported: dict[str, Path] = {}

    for stage_name, result in campaign.results.items():
        artifact = result.artifact

        if stage_name == "research":
            content = _format_research_md(artifact, campaign)
            layout.research_report.write_text(content)
            exported["research"] = layout.research_report

        elif stage_name == "strategy":
            content = _format_strategy_md(artifact, campaign)
            layout.strategy_brief.write_text(content)
            exported["strategy"] = layout.strategy_brief

        elif stage_name == "creative":
            content = _format_creative_md(artifact, campaign)
            layout.copy_deck.write_text(content)
            exported["creative"] = layout.copy_deck

        elif stage_name == "activation":
            content = _format_activation_md(artifact, campaign)
            layout.activation_plan.write_text(content)
            exported["activation"] = layout.activation_plan

    # Create campaign summary
    summary = _format_summary_md(campaign, exported)
    layout.package_brief.write_text(summary)
    exported["summary"] = layout.package_brief

    return exported


def _format_research_md(artifact: dict[str, Any], campaign: Campaign) -> str:
    """Format research report as markdown."""
    lines = [
        "# Research Report",
        "",
        f"> Campaign: {campaign.id}",
        f"> Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
    ]

    # Insights
    insights = artifact.get("insights", [])
    if insights:
        lines.append("## Key Insights")
        lines.append("")
        for i, insight in enumerate(insights, 1):
            lines.append(f"{i}. {insight}")
        lines.append("")

    # Competitors
    competitors = artifact.get("competitors", [])
    if competitors:
        lines.append("## Competitor Analysis")
        lines.append("")
        for comp in competitors:
            lines.append(f"### {comp.get('name', 'Competitor')}")
            lines.append("")
            lines.append(f"**Positioning:** {comp.get('positioning', 'N/A')}")
            lines.append("")
            strengths = comp.get("strengths", [])
            if strengths:
                lines.append("**Strengths:**")
                for s in strengths:
                    lines.append(f"- {s}")
            weaknesses = comp.get("weaknesses", [])
            if weaknesses:
                lines.append("")
                lines.append("**Weaknesses:**")
                for w in weaknesses:
                    lines.append(f"- {w}")
            lines.append("")

    # Sources
    sources = artifact.get("sources", [])
    if sources:
        lines.append("## Sources")
        lines.append("")
        for source in sources:
            title = source.get("title", "Source")
            url = source.get("url", "")
            snippet = source.get("snippet", "")
            if url:
                lines.append(f"- [{title}]({url})")
            else:
                lines.append(f"- {title}")
            if snippet:
                lines.append(f"  > {snippet[:100]}...")
        lines.append("")

    # Assumptions
    assumptions = artifact.get("assumptions", [])
    if assumptions:
        lines.append("## Assumptions")
        lines.append("")
        for a in assumptions:
            lines.append(f"- {a}")
        lines.append("")

    return "\n".join(lines)


def _format_strategy_md(artifact: dict[str, Any], campaign: Campaign) -> str:
    """Format strategy brief as markdown."""
    lines = [
        "# Strategy Brief",
        "",
        f"> Campaign: {campaign.id}",
        f"> Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
    ]

    # Positioning
    positioning = artifact.get("positioning", "")
    if positioning:
        lines.append("## Positioning Statement")
        lines.append("")
        lines.append(f"> {positioning}")
        lines.append("")

    # Target Audience
    audience = artifact.get("target_audience", {})
    if audience:
        lines.append("## Target Audience")
        lines.append("")
        lines.append(f"**Name:** {audience.get('name', 'N/A')}")
        lines.append(f"**Demographics:** {audience.get('demographics', 'N/A')}")
        lines.append("")
        pain_points = audience.get("pain_points", [])
        if pain_points:
            lines.append("**Pain Points:**")
            for p in pain_points:
                lines.append(f"- {p}")
            lines.append("")
        motivations = audience.get("motivations", [])
        if motivations:
            lines.append("**Motivations:**")
            for m in motivations:
                lines.append(f"- {m}")
            lines.append("")

    # Messaging Pillars
    pillars = artifact.get("messaging_pillars", [])
    if pillars:
        lines.append("## Messaging Pillars")
        lines.append("")
        for i, pillar in enumerate(pillars, 1):
            lines.append(f"{i}. **{pillar}**")
        lines.append("")

    # Proof Points
    proof_points = artifact.get("proof_points", [])
    if proof_points:
        lines.append("## Proof Points")
        lines.append("")
        for p in proof_points:
            lines.append(f"- {p}")
        lines.append("")

    # Risks
    risks = artifact.get("risks", [])
    if risks:
        lines.append("## Risks & Mitigation")
        lines.append("")
        for r in risks:
            lines.append(f"- {r}")
        lines.append("")

    return "\n".join(lines)


def _format_creative_md(artifact: dict[str, Any], campaign: Campaign) -> str:
    """Format copy deck as markdown."""
    lines = [
        "# Copy Deck",
        "",
        f"> Campaign: {campaign.id}",
        f"> Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"> Brand Voice Score: {artifact.get('brand_voice_score', 0):.0%}",
        "",
    ]

    # Headlines
    headlines = artifact.get("headline_variants", [])
    if headlines:
        lines.append("## Headlines")
        lines.append("")
        for i, h in enumerate(headlines, 1):
            lines.append(f"{i}. **{h}**")
        lines.append("")

    # Body Copy
    body_variants = artifact.get("body_variants", [])
    if body_variants:
        lines.append("## Body Copy")
        lines.append("")
        for i, body in enumerate(body_variants, 1):
            lines.append(f"### Variant {i}")
            lines.append("")
            lines.append(body)
            lines.append("")

    # CTAs
    ctas = artifact.get("cta_variants", [])
    if ctas:
        lines.append("## Calls to Action")
        lines.append("")
        for cta in ctas:
            lines.append(f"- `{cta}`")
        lines.append("")

    return "\n".join(lines)


def _format_activation_md(artifact: dict[str, Any], campaign: Campaign) -> str:
    """Format activation plan as markdown."""
    lines = [
        "# Activation Plan",
        "",
        f"> Campaign: {campaign.id}",
        f"> Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
    ]

    # Channels
    channels = artifact.get("channels", [])
    if channels:
        lines.append("## Channel Strategy")
        lines.append("")
        for ch in channels:
            lines.append(f"### {ch.get('channel', 'Channel')}")
            lines.append("")
            lines.append(f"**Objective:** {ch.get('objective', 'N/A')}")
            budget = ch.get("budget_pct", 0)
            if budget:
                lines.append(f"**Budget:** {budget:.0%}")
            lines.append("")
            tactics = ch.get("tactics", [])
            if tactics:
                lines.append("**Tactics:**")
                for t in tactics:
                    lines.append(f"- {t}")
            lines.append("")

    # Content Calendar
    calendar = artifact.get("content_calendar", [])
    if calendar:
        lines.append("## Content Calendar")
        lines.append("")
        lines.append("| Date | Channel | Type | Description |")
        lines.append("|------|---------|------|-------------|")
        for entry in calendar:
            lines.append(
                f"| {entry.get('date', '')} | {entry.get('channel', '')} | "
                f"{entry.get('content_type', '')} | {entry.get('description', '')} |"
            )
        lines.append("")

    # KPIs
    kpis = artifact.get("kpis", [])
    if kpis:
        lines.append("## KPIs & Targets")
        lines.append("")
        lines.append("| Metric | Target | Measurement |")
        lines.append("|--------|--------|-------------|")
        for kpi in kpis:
            lines.append(
                f"| {kpi.get('metric', '')} | {kpi.get('target', '')} | "
                f"{kpi.get('measurement', '')} |"
            )
        lines.append("")

    # Budget Allocation
    budget = artifact.get("budget_allocation", {})
    if budget:
        lines.append("## Budget Allocation")
        lines.append("")
        for channel, pct in budget.items():
            lines.append(f"- **{channel}:** {pct:.0%}")
        lines.append("")

    return "\n".join(lines)


def _format_summary_md(campaign: Campaign, exported: dict[str, Path]) -> str:
    """Format campaign summary as markdown."""
    lines = [
        "# Campaign Summary",
        "",
        f"**Campaign ID:** {campaign.id}",
        f"**Template:** {campaign.template}",
        f"**Brief:** {campaign.brief}",
        "",
        f"**Created:** {campaign.created_at.strftime('%Y-%m-%d %H:%M')}",
        f"**Updated:** {campaign.updated_at.strftime('%Y-%m-%d %H:%M')}",
        "",
    ]

    if campaign.brand_name:
        lines.append(f"**Brand:** {campaign.brand_name}")
        lines.append("")

    if campaign.total_tokens > 0:
        lines.append("## Usage")
        lines.append("")
        lines.append(f"- **Tokens:** {campaign.total_tokens:,}")
        lines.append(f"- **Cost:** ${campaign.total_cost_usd:.4f}")
        lines.append("")

    lines.append("## Deliverables")
    lines.append("")
    for name, path in exported.items():
        if name != "summary":
            lines.append(f"- [{name.title()}]({path.name})")
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("*Generated by Agentcy*")

    return "\n".join(lines)


def export_to_format(
    campaign: Campaign,
    output_dir: Path,
    format: str = "md",
) -> dict[str, Path]:
    """Export campaign to specified format.

    Args:
        campaign: Campaign to export
        output_dir: Output directory
        format: Export format (md, pdf, notion)

    Returns:
        Dict of exported file paths

    Raises:
        ValueError: If format not supported
    """
    if format == "md":
        return export_markdown(campaign, output_dir)
    elif format == "pdf":
        raise ValueError("PDF export not yet implemented")
    elif format == "notion":
        raise ValueError("Notion export not yet implemented")
    else:
        raise ValueError(f"Unknown format: {format}")
