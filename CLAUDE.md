# CLAUDE.md

AI marketing agency. Agent-first by default, HITL optional.

## Stack

| Layer | Tech |
|-------|------|
| LLM | Gemini 3 Flash (google-genai SDK) |
| CLI | Typer + Rich |
| Persistence | JSON files (.agency/) |
| Schemas | Pydantic v2 |
| Package | uv + hatchling |
| Python | 3.12+ |

## Commands

```bash
# Install
uv sync

# Agent mode (default) - runs to completion, outputs JSON
agency run "Launch AI product to devs"
agency run "Brief" -o campaign.json

# Interactive mode - human gates at each stage
agency run "Brief" --interactive

# Individual stages (pipeable)
agency research "AI dev tools market"
agency research "Brief" | agency strategy
agency strategy < research.json | agency creative

# Resume interactive session
agency resume <campaign-id>

# List saved campaigns
agency list

# Lint/format
uv run ruff check agency/
uv run ruff format agency/
```

## Architecture

```
agency/
├── __init__.py       # Public API: research, strategy, creative, activate, run
├── cli.py            # Typer CLI
├── stages/
│   ├── research.py   # Market research → ResearchResult
│   ├── strategy.py   # Positioning → StrategyResult
│   ├── creative.py   # Copy generation → CreativeResult
│   └── activation.py # Channel planning → ActivationResult
├── core/
│   ├── llm.py        # Gemini client with structured output
│   └── store.py      # JSON persistence for --interactive
└── ui/
    └── prompts.py    # HITL gates (only with --interactive)
```

## Python API

```python
from agency import research, strategy, creative, activate, run

# Full pipeline
result = run("Launch AI product to devs")

# Individual stages
r = research("AI dev tools market")
s = strategy(r)
c = creative(s)
a = activate(s, c)
```

## Environment

```bash
# Required
GOOGLE_API_KEY=...           # Gemini

# Optional
SERPER_API_KEY=...           # Web search
AGENCY_LIVE_TOOLS=1          # Use live APIs (default: stubs)
```

## Key Patterns

- **Agent-first**: Non-interactive by default, outputs JSON
- **Composable**: Each stage is a pure function returning Pydantic models
- **Pipeable**: `research | strategy | creative | activate`
- **HITL optional**: `--interactive` enables human gates
