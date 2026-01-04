# Agentcy

AI-powered marketing campaign generator with human approval gates.

## Overview

Agentcy transforms a brief into a complete campaign package using specialized AI agents. Each stage requires human approval before proceeding, ensuring quality and alignment.

**Key Features:**
- **6 Specialized Agents**: Researcher, Strategist, Copywriter, Visual Director, Marketer, Critic
- **Human-in-the-Loop**: Approve, edit, or regenerate at each stage
- **Resumable Sessions**: Save progress and continue later
- **Brand Voice Compliance**: Validates copy against brand guidelines
- **Quality Rubrics**: Structured evaluation criteria per artifact

## Quick Start

```bash
# Install
uv sync

# Run a campaign
agentcy run --brief "Launch our new productivity app for remote teams"

# Resume a paused campaign
agentcy resume <campaign-id>

# List campaigns
agentcy list
```

## Workflow

```
INTAKE → RESEARCH → STRATEGY → CREATIVE → ACTIVATION → PACKAGING → DONE
           ↓           ↓           ↓            ↓            ↓
        [Gate]      [Gate]      [Gate]       [Gate]       [Gate]
```

At each gate you can:
- **[A]pprove** - Accept and continue
- **[E]dit** - Modify the artifact
- **[R]egenerate** - Generate a new version
- **[S]kip** - Bypass this stage
- **[Q]uit** - Save and exit

## Commands

```bash
# Initialize with brand kit
agentcy init --template product-launch --brand ./brand/

# Run with all options
agentcy run \
  --brief "Your campaign brief" \
  --brand ./brand/ \
  --output ./campaigns/ \
  --template product-launch

# Export to different formats
agentcy export ./campaigns/my-campaign/ --format md
```

## Configuration

### Brand Kit (brand/brand.yaml)

```yaml
name: "Acme Corp"
tagline: "Innovation delivered"
industry: "B2B SaaS"
target_audience: "CTOs at mid-market companies"

voice:
  tone:
    - professional
    - confident
    - approachable
  avoid:
    - jargon
    - buzzwords
    - synergy
```

### Global Config (~/.agentcy/config.yaml)

```yaml
models:
  default: gemini-3-flash-preview
  research: gemini-2.5-flash-lite
  creative: gemini-3-flash-preview
  critic: gemini-3-flash-preview

output_dir: ./campaigns/
```

## Templates

### Product Launch (default)

Stages:
1. **Research**: Market analysis, competitors, audience insights
2. **Strategy**: Positioning, messaging pillars, target persona
3. **Creative**: Headlines, body copy, CTAs
4. **Activation**: Channel mix, content calendar, KPIs

## Output Structure

```
campaigns/<campaign-id>/
├── campaign.json         # Campaign state (resumable)
├── research/
│   └── report.md         # Research findings
├── strategy/
│   └── brief.md          # Strategy brief
├── creative/
│   └── copy.md           # Copy deck
├── activation/
│   └── plan.md           # Activation plan
└── package/
    └── brief.md          # Campaign summary
```

## Environment Variables

```bash
# Required for live tools
GOOGLE_API_KEY=your_gemini_key

# Optional
SERPER_API_KEY=your_serper_key     # Web search
REPLICATE_API_TOKEN=your_token     # Image generation

# Development
AGENTCY_LIVE_TOOLS=1               # Use live APIs (default: stubs)
```

## Development

```bash
# Install dev dependencies
uv sync --dev

# Run tests
uv run pytest tests/ -v

# Type check
uv run mypy agentcy/

# Format
uv run ruff format agentcy/
```

## Architecture

Built on [Agno](https://github.com/agno-agi/agno) with a custom state machine controller:

- **Agents**: Agno agents with structured outputs (Pydantic)
- **Controller**: Python state machine with stage transitions
- **Persistence**: SQLite for campaign state
- **Gates**: Rich CLI for human-in-the-loop approval

## License

MIT
