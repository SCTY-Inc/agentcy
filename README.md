# Agency

AI marketing agency. Agent-first by default, human-in-the-loop optional.

## Quick Start

```bash
# Install
uv sync

# Run full pipeline (outputs JSON)
agency run "Launch AI product to developers"

# Save to file
agency run "Brief" -o campaign.json

# Interactive mode (human gates)
agency run "Brief" --interactive
```

## CLI

```bash
# Full pipeline
agency run "Brief"                    # Non-interactive, outputs JSON
agency run "Brief" -i                 # Interactive with approval gates
agency run "Brief" -o out.json        # Save to file

# Individual stages (pipeable)
agency research "AI dev tools market"
agency research "Brief" | agency strategy
agency strategy < research.json | agency creative
agency creative < strategy.json | agency activate -s strategy.json

# Interactive sessions
agency list                           # List saved campaigns
agency resume <id>                    # Resume interactive session
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

## Pipeline

```
Brief (str)
    │
    ▼
┌─────────────┐
│  research   │ → ResearchResult (insights, competitors, sources)
└─────────────┘
    │
    ▼
┌─────────────┐
│  strategy   │ → StrategyResult (positioning, audience, pillars)
└─────────────┘
    │
    ▼
┌─────────────┐
│  creative   │ → CreativeResult (headlines, body copy, CTAs)
└─────────────┘
    │
    ▼
┌─────────────┐
│  activate   │ → ActivationResult (channels, calendar, KPIs)
└─────────────┘
    │
    ▼
JSON output
```

## Environment

```bash
# Required
GOOGLE_API_KEY=...           # Gemini API key

# Optional
AGENCY_MODEL=gemini-2.0-flash  # Override default model
SERPER_API_KEY=...             # Live web search
AGENCY_LIVE_TOOLS=1            # Enable live APIs (default: stubs)
```

## Development

```bash
uv sync --dev
uv run ruff check agency/
uv run ruff format agency/
```

## History

| Date | Version | Changes |
|------|---------|---------|
| 2026-01-25 | v4.0 | Rewrite as agent-first CLI. Non-interactive default, `--interactive` flag for HITL. Composable stages. JSON file storage. |
| 2026-01-04 | v3.1 | Add Agno Culture for shared agent knowledge. Improvement beads. |
| 2026-01-03 | v3.0 | Migrate to Agno framework. 6 specialized agents. SQLite persistence. Quality rubrics. |
| 2026-01-03 | v2.0 | Switch from OpenAI/Anthropic to Gemini. Add controller + gates. |
| 2025-08-03 | v1.0 | Migrate to AG2 (AutoGen rebrand). Consolidate experimental packages. |
| 2023-10-12 | v0.2 | Add RAG web search for research. Chat logging. |
| 2023-09-27 | v0.1 | Initial POC. AutoGen group chat with Researcher, Strategist, Copywriter, Art Director, Marketer agents. OpenAI GPT-4. |

## License

MIT
