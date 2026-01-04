"""Campaign state machine controller.

Custom orchestrator (NOT Agno Workflows) that manages:
    - Stage transitions: INTAKE -> RESEARCH -> STRATEGY -> CREATIVE -> ACTIVATION -> PACKAGING -> DONE
    - Human gates at each transition (approve/edit/regen)
    - Persistence to SQLite
    - Resume capability
"""

import hashlib
import json
from datetime import datetime
from typing import Any, Callable

from pydantic import BaseModel

from agentcy.config import AgentcyConfig, load_config
from agentcy.models.artifacts import (
    ActivationPlan,
    CopyDeck,
    ResearchReport,
    StrategyBrief,
)
from agentcy.models.brand import BrandKit
from agentcy.models.campaign import Campaign, StageResult
from agentcy.models.stages import (
    Stage,
    StageTransitionError,
    next_stage,
    validate_transition,
)


class StageExecutionError(Exception):
    """Stage execution failed."""

    def __init__(self, stage: Stage, message: str, retryable: bool = True):
        self.stage = stage
        self.retryable = retryable
        super().__init__(f"Stage {stage.value} failed: {message}")


class CampaignController:
    """Orchestrates campaign workflow through stages.

    This is a custom state machine (not Agno Workflows) because:
    1. Agno HITL only supports Agents, not Workflows
    2. We need full control over persistence
    3. CLI gates require synchronous prompts
    """

    def __init__(
        self,
        campaign: Campaign,
        brand: BrandKit | None = None,
        config: AgentcyConfig | None = None,
        on_stage_complete: Callable[[Stage, Any], None] | None = None,
        on_stage_error: Callable[[Stage, Exception], None] | None = None,
    ):
        """Initialize controller.

        Args:
            campaign: Campaign state object
            brand: Brand kit for voice guidelines
            config: Agentcy configuration
            on_stage_complete: Callback after stage completes
            on_stage_error: Callback on stage error
        """
        self.campaign = campaign
        self.brand = brand
        self.config = config or load_config()
        self.on_stage_complete = on_stage_complete
        self.on_stage_error = on_stage_error

    @property
    def current_stage(self) -> Stage:
        """Get current campaign stage."""
        return self.campaign.current_stage

    @property
    def is_complete(self) -> bool:
        """Check if campaign is done."""
        return self.campaign.current_stage == Stage.DONE

    def get_stage_result(self, stage: Stage) -> StageResult | None:
        """Get result for a completed stage."""
        return self.campaign.results.get(stage.value)

    def has_stage_result(self, stage: Stage) -> bool:
        """Check if stage has a result."""
        return stage.value in self.campaign.results

    def compute_inputs_hash(self, inputs: dict[str, Any]) -> str:
        """Compute hash of stage inputs for idempotency.

        Args:
            inputs: Stage input data

        Returns:
            SHA256 hash of JSON-serialized inputs
        """
        serialized = json.dumps(inputs, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode()).hexdigest()[:16]

    def is_idempotent(self, stage: Stage, inputs: dict[str, Any]) -> bool:
        """Check if stage already has result for these inputs.

        Args:
            stage: Stage to check
            inputs: Stage input data

        Returns:
            True if stage has matching result
        """
        result = self.get_stage_result(stage)
        if not result:
            return False
        current_hash = self.compute_inputs_hash(inputs)
        return result.inputs_hash == current_hash

    def advance(self) -> Stage | None:
        """Advance to next stage if current is approved.

        Returns:
            New stage, or None if at DONE

        Raises:
            StageTransitionError: If current stage not approved
        """
        current = self.current_stage
        target = next_stage(current)

        if target is None:
            return None

        # Verify current stage is approved (except INTAKE)
        if current != Stage.INTAKE:
            result = self.get_stage_result(current)
            if not result or not result.approved:
                raise StageTransitionError(
                    current, target
                )  # Will show "not approved" in error

        validate_transition(current, target)
        self.campaign.current_stage = target
        self.campaign.updated_at = datetime.now()

        return target

    def record_result(
        self,
        stage: Stage,
        artifact: BaseModel | dict[str, Any],
        approved: bool = False,
        inputs_hash: str | None = None,
    ) -> StageResult:
        """Record a stage result.

        Args:
            stage: Stage that produced the result
            artifact: Stage output (Pydantic model or dict)
            approved: Whether human approved this result
            inputs_hash: Hash for idempotency checking

        Returns:
            Created StageResult
        """
        if isinstance(artifact, BaseModel):
            artifact_dict = artifact.model_dump()
        else:
            artifact_dict = artifact

        result = StageResult(
            stage=stage,
            artifact=artifact_dict,
            approved=approved,
            approved_at=datetime.now() if approved else None,
            inputs_hash=inputs_hash,
        )

        self.campaign.results[stage.value] = result
        self.campaign.updated_at = datetime.now()

        if self.on_stage_complete:
            self.on_stage_complete(stage, artifact)

        return result

    def approve_stage(self, stage: Stage) -> StageResult | None:
        """Mark a stage as approved.

        Args:
            stage: Stage to approve

        Returns:
            Updated StageResult, or None if stage has no result
        """
        result = self.get_stage_result(stage)
        if not result:
            return None

        result.approved = True
        result.approved_at = datetime.now()
        self.campaign.results[stage.value] = result
        self.campaign.updated_at = datetime.now()

        return result

    def run_stage(self, stage: Stage, inputs: dict[str, Any]) -> BaseModel:
        """Execute a single stage.

        Args:
            stage: Stage to run
            inputs: Stage-specific inputs

        Returns:
            Stage artifact

        Raises:
            StageExecutionError: If stage fails
        """
        # Check idempotency
        if self.is_idempotent(stage, inputs):
            result = self.get_stage_result(stage)
            if result:
                # Return cached result
                return self._deserialize_artifact(stage, result.artifact)

        inputs_hash = self.compute_inputs_hash(inputs)

        try:
            artifact = self._execute_stage(stage, inputs)
            self.record_result(stage, artifact, approved=False, inputs_hash=inputs_hash)
            return artifact
        except Exception as e:
            if self.on_stage_error:
                self.on_stage_error(stage, e)
            raise StageExecutionError(stage, str(e)) from e

    def _execute_stage(self, stage: Stage, inputs: dict[str, Any]) -> BaseModel:
        """Internal stage execution dispatcher.

        Args:
            stage: Stage to execute
            inputs: Stage inputs

        Returns:
            Stage artifact
        """
        executors = {
            Stage.RESEARCH: self._run_research,
            Stage.STRATEGY: self._run_strategy,
            Stage.CREATIVE: self._run_creative,
            Stage.ACTIVATION: self._run_activation,
            Stage.PACKAGING: self._run_packaging,
        }

        executor = executors.get(stage)
        if not executor:
            raise StageExecutionError(
                stage, f"No executor for stage {stage.value}", retryable=False
            )

        return executor(inputs)

    def _run_research(self, inputs: dict[str, Any]) -> ResearchReport:
        """Execute research stage."""
        from agentcy.agents.researcher import run_research

        return run_research(
            brief=self.campaign.brief,
            campaign_id=self.campaign.id,
            model_id=self.config.models.research,
        )

    def _run_strategy(self, inputs: dict[str, Any]) -> StrategyBrief:
        """Execute strategy stage."""
        from agentcy.agents.strategist import run_strategy

        research_result = self.get_stage_result(Stage.RESEARCH)
        research_summary = ""
        if research_result:
            insights = research_result.artifact.get("insights", [])
            research_summary = "\n".join(f"- {i}" for i in insights)

        return run_strategy(
            brief=self.campaign.brief,
            research_summary=research_summary,
            campaign_id=self.campaign.id,
            model_id=self.config.models.default,
        )

    def _run_creative(self, inputs: dict[str, Any]) -> CopyDeck:
        """Execute creative stage."""
        from agentcy.agents.copywriter import run_copywriting

        strategy_result = self.get_stage_result(Stage.STRATEGY)
        strategy_brief = ""
        if strategy_result:
            artifact = strategy_result.artifact
            strategy_brief = f"""
Positioning: {artifact.get('positioning', '')}
Messaging Pillars: {', '.join(artifact.get('messaging_pillars', []))}
"""

        return run_copywriting(
            strategy_brief=strategy_brief,
            campaign_id=self.campaign.id,
            brand=self.brand,
            model_id=self.config.models.creative,
        )

    def _run_activation(self, inputs: dict[str, Any]) -> ActivationPlan:
        """Execute activation stage."""
        from agentcy.agents.marketer import run_activation_planning

        strategy_result = self.get_stage_result(Stage.STRATEGY)
        creative_result = self.get_stage_result(Stage.CREATIVE)

        strategy_brief = ""
        if strategy_result:
            strategy_brief = strategy_result.artifact.get("positioning", "")

        copy_summary = ""
        if creative_result:
            headlines = creative_result.artifact.get("headline_variants", [])
            copy_summary = "\n".join(headlines[:3])

        return run_activation_planning(
            strategy_brief=strategy_brief,
            copy_summary=copy_summary,
            campaign_id=self.campaign.id,
            model_id=self.config.models.default,
        )

    def _run_packaging(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Execute packaging stage - exports all artifacts."""
        from agentcy.persistence.layout import CampaignLayout
        from pathlib import Path

        # Create campaign directory
        output_dir = self.config.output_dir / self.campaign.id
        layout = CampaignLayout(output_dir)

        # Export each artifact
        exported = {}
        for stage_name, result in self.campaign.results.items():
            stage = Stage(stage_name)
            artifact = result.artifact

            if stage == Stage.RESEARCH:
                content = self._format_research(artifact)
                layout.research_report.write_text(content)
                exported["research"] = str(layout.research_report)
            elif stage == Stage.STRATEGY:
                content = self._format_strategy(artifact)
                layout.strategy_brief.write_text(content)
                exported["strategy"] = str(layout.strategy_brief)
            elif stage == Stage.CREATIVE:
                content = self._format_creative(artifact)
                layout.copy_deck.write_text(content)
                exported["creative"] = str(layout.copy_deck)
            elif stage == Stage.ACTIVATION:
                content = self._format_activation(artifact)
                layout.activation_plan.write_text(content)
                exported["activation"] = str(layout.activation_plan)

        # Create package summary
        summary = self._create_package_summary(exported)
        layout.package_brief.write_text(summary)
        exported["package"] = str(layout.package_brief)

        return {"files": exported, "campaign_id": self.campaign.id}

    def _format_research(self, artifact: dict[str, Any]) -> str:
        """Format research artifact as markdown."""
        lines = ["# Research Report", ""]
        lines.append("## Key Insights")
        for insight in artifact.get("insights", []):
            lines.append(f"- {insight}")
        lines.append("")
        lines.append("## Sources")
        for source in artifact.get("sources", []):
            lines.append(f"- [{source.get('title', 'Source')}]({source.get('url', '')})")
        return "\n".join(lines)

    def _format_strategy(self, artifact: dict[str, Any]) -> str:
        """Format strategy artifact as markdown."""
        lines = ["# Strategy Brief", ""]
        lines.append(f"## Positioning\n{artifact.get('positioning', '')}\n")
        lines.append("## Messaging Pillars")
        for pillar in artifact.get("messaging_pillars", []):
            lines.append(f"- {pillar}")
        return "\n".join(lines)

    def _format_creative(self, artifact: dict[str, Any]) -> str:
        """Format creative artifact as markdown."""
        lines = ["# Copy Deck", ""]
        lines.append("## Headlines")
        for h in artifact.get("headline_variants", []):
            lines.append(f"- {h}")
        lines.append("")
        lines.append("## Body Copy")
        for b in artifact.get("body_variants", []):
            lines.append(f"\n{b}\n")
        lines.append("## CTAs")
        for c in artifact.get("cta_variants", []):
            lines.append(f"- {c}")
        return "\n".join(lines)

    def _format_activation(self, artifact: dict[str, Any]) -> str:
        """Format activation artifact as markdown."""
        lines = ["# Activation Plan", ""]
        lines.append("## Channels")
        for ch in artifact.get("channels", []):
            lines.append(f"### {ch.get('channel', 'Channel')}")
            lines.append(f"Objective: {ch.get('objective', '')}")
            lines.append("Tactics:")
            for t in ch.get("tactics", []):
                lines.append(f"- {t}")
            lines.append("")
        return "\n".join(lines)

    def _create_package_summary(self, exported: dict[str, str]) -> str:
        """Create package summary markdown."""
        lines = [
            f"# Campaign Package: {self.campaign.id}",
            "",
            f"Brief: {self.campaign.brief}",
            "",
            "## Deliverables",
            "",
        ]
        for name, path in exported.items():
            lines.append(f"- {name}: {path}")
        return "\n".join(lines)

    def _deserialize_artifact(self, stage: Stage, artifact: dict[str, Any]) -> BaseModel:
        """Deserialize artifact dict back to Pydantic model."""
        artifact_types = {
            Stage.RESEARCH: ResearchReport,
            Stage.STRATEGY: StrategyBrief,
            Stage.CREATIVE: CopyDeck,
            Stage.ACTIVATION: ActivationPlan,
        }
        model_class = artifact_types.get(stage)
        if model_class:
            return model_class(**artifact)
        # For packaging, return as-is wrapped in a simple model
        from pydantic import BaseModel as BM

        class PackageResult(BM):
            files: dict[str, str]
            campaign_id: str

        return PackageResult(**artifact)
