"""End-to-end integration tests for Agentcy.

These tests verify the complete workflow without live API calls.
"""

import tempfile
from pathlib import Path

import pytest

from agentcy.config import AgentcyConfig
from agentcy.controller import CampaignController
from agentcy.export import export_markdown
from agentcy.models.artifacts import (
    ActivationPlan,
    ChannelPlan,
    CopyDeck,
    ResearchReport,
    Source,
    StrategyBrief,
    AudiencePersona,
)
from agentcy.models.brand import BrandKit, VoiceGuidelines
from agentcy.models.campaign import Campaign
from agentcy.models.stages import Stage, next_stage, validate_transition
from agentcy.persistence import CampaignStore
from agentcy.quality import validate_brand_voice, score_artifact
from agentcy.templates import load_template


class TestCampaignFlow:
    """Test complete campaign workflow."""

    def test_campaign_creation(self):
        """Test creating a new campaign."""
        campaign = Campaign(
            id="test-integration-001",
            brief="Launch a new productivity app",
            template="product-launch",
        )

        assert campaign.id == "test-integration-001"
        assert campaign.current_stage == Stage.INTAKE
        assert len(campaign.results) == 0

    def test_stage_transitions(self):
        """Test valid stage transitions."""
        campaign = Campaign(id="test-002", brief="Test")

        # INTAKE -> RESEARCH
        assert next_stage(Stage.INTAKE) == Stage.RESEARCH
        validate_transition(Stage.INTAKE, Stage.RESEARCH)

        # RESEARCH -> STRATEGY
        assert next_stage(Stage.RESEARCH) == Stage.STRATEGY
        validate_transition(Stage.RESEARCH, Stage.STRATEGY)

        # Full chain
        current = Stage.INTAKE
        expected = [Stage.RESEARCH, Stage.STRATEGY, Stage.CREATIVE, Stage.ACTIVATION, Stage.PACKAGING, Stage.DONE]
        for expected_next in expected:
            assert next_stage(current) == expected_next
            current = expected_next

    def test_controller_with_mocked_results(self):
        """Test controller with manually added results."""
        campaign = Campaign(id="test-003", brief="Test campaign")
        config = AgentcyConfig()
        controller = CampaignController(campaign=campaign, config=config)

        # Manually add research result
        research = ResearchReport(
            campaign_id=campaign.id,
            sources=[Source(url="https://example.com", title="Source 1")],
            insights=["Insight 1", "Insight 2", "Insight 3"],
        )
        controller.record_result(Stage.RESEARCH, research, approved=True)

        assert controller.has_stage_result(Stage.RESEARCH)
        result = controller.get_stage_result(Stage.RESEARCH)
        assert result is not None
        assert result.approved


class TestPersistence:
    """Test campaign persistence."""

    def test_save_and_load_campaign(self):
        """Test saving and loading a campaign."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        store = CampaignStore(db_path)

        # Create and save campaign
        campaign = Campaign(
            id="persist-test-001",
            brief="Test persistence",
            brand_name="TestBrand",
            template="product-launch",
        )
        store.save(campaign)

        # Load and verify
        loaded = store.load("persist-test-001")
        assert loaded is not None
        assert loaded.id == campaign.id
        assert loaded.brief == campaign.brief
        assert loaded.brand_name == "TestBrand"
        assert loaded.current_stage == Stage.INTAKE

    def test_save_with_results(self):
        """Test saving campaign with stage results."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        store = CampaignStore(db_path)
        config = AgentcyConfig()

        campaign = Campaign(id="persist-test-002", brief="Test with results")
        controller = CampaignController(campaign=campaign, config=config)

        # Add and approve a result
        research = ResearchReport(
            campaign_id=campaign.id,
            insights=["Insight 1"],
        )
        controller.record_result(Stage.RESEARCH, research, approved=True)
        controller.campaign.current_stage = Stage.STRATEGY

        store.save(campaign)

        # Load and verify
        loaded = store.load("persist-test-002")
        assert loaded is not None
        assert loaded.current_stage == Stage.STRATEGY
        assert Stage.RESEARCH.value in loaded.results
        assert loaded.results[Stage.RESEARCH.value].approved


class TestQuality:
    """Test quality validation."""

    def test_brand_voice_validation(self):
        """Test brand voice validation."""
        brand = BrandKit(
            name="TestBrand",
            voice=VoiceGuidelines(
                tone=["professional", "confident"],
                avoid=["synergy", "leverage", "disrupt"],
            ),
        )

        # Good copy
        good_copy = "Our proven solution delivers guaranteed results for your business."
        result = validate_brand_voice(good_copy, brand)
        assert result.passed
        assert len(result.violations) == 0

        # Bad copy with avoided words
        bad_copy = "Let's leverage synergy to disrupt the market."
        result = validate_brand_voice(bad_copy, brand)
        assert not result.passed
        assert len(result.violations) == 3

    def test_rubric_scoring(self):
        """Test artifact scoring against rubrics."""
        # Research with all criteria met
        result = score_artifact(
            "research",
            {
                "sources": 1.0,  # 5+ sources
                "insights": 0.9,  # 3+ insights
                "competitors": 0.8,  # Competitors analyzed
                "assumptions": 0.7,  # Assumptions stated
                "claims": 0.8,  # No unsubstantiated claims
            },
        )
        assert result.passed
        assert result.overall_score > 0.7

        # Research missing required items
        result = score_artifact(
            "research",
            {
                "sources": 0.3,  # Fewer than 5 sources
                "insights": 0.2,  # Fewer than 3 insights
                "competitors": 0.5,
                "assumptions": 0.5,
                "claims": 0.5,
            },
        )
        assert not result.passed
        assert "sources" in result.required_failures
        assert "insights" in result.required_failures


class TestExport:
    """Test markdown export."""

    def test_export_markdown(self):
        """Test exporting campaign to markdown."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)

            # Create campaign with results
            campaign = Campaign(
                id="export-test-001",
                brief="Test export functionality",
            )

            # Add mock results
            from agentcy.models.campaign import StageResult

            campaign.results["research"] = StageResult(
                stage=Stage.RESEARCH,
                artifact={
                    "campaign_id": campaign.id,
                    "insights": ["Insight 1", "Insight 2"],
                    "sources": [{"url": "https://example.com", "title": "Source"}],
                    "competitors": [],
                    "assumptions": ["Assumption 1"],
                },
                approved=True,
            )

            campaign.results["strategy"] = StageResult(
                stage=Stage.STRATEGY,
                artifact={
                    "campaign_id": campaign.id,
                    "positioning": "The leading solution for X",
                    "target_audience": {
                        "name": "Tech Leaders",
                        "demographics": "25-45",
                        "pain_points": ["Pain 1"],
                        "motivations": ["Motivation 1"],
                    },
                    "messaging_pillars": ["Pillar 1", "Pillar 2", "Pillar 3"],
                    "proof_points": ["Proof 1"],
                    "risks": [],
                },
                approved=True,
            )

            # Export
            exported = export_markdown(campaign, output_dir)

            # Verify files created
            assert "research" in exported
            assert exported["research"].exists()
            assert "# Research Report" in exported["research"].read_text()

            assert "strategy" in exported
            assert exported["strategy"].exists()
            assert "# Strategy Brief" in exported["strategy"].read_text()

            assert "summary" in exported
            assert exported["summary"].exists()


class TestTemplates:
    """Test template loading."""

    def test_load_product_launch_template(self):
        """Test loading the product-launch template."""
        template = load_template("product-launch")

        assert template.name == "product-launch"
        assert "research" in template.stages
        assert "strategy" in template.stages
        assert "creative" in template.stages
        assert "activation" in template.stages

    def test_template_prompts(self):
        """Test loading template prompts."""
        template = load_template("product-launch")

        research_prompt = template.get_prompt("research")
        assert research_prompt is not None
        assert "Market Analysis" in research_prompt

        strategy_prompt = template.get_prompt("strategy")
        assert strategy_prompt is not None
        assert "Positioning" in strategy_prompt

    def test_template_exit_criteria(self):
        """Test template exit criteria."""
        template = load_template("product-launch")

        research_criteria = template.get_exit_criteria("research")
        assert "min_sources" in research_criteria
        assert research_criteria["min_sources"] == 5


class TestObservability:
    """Test observability features."""

    def test_trace_id_generation(self):
        """Test trace ID generation and context."""
        from agentcy.observability import get_trace_id, set_trace_id, generate_trace_id

        # Generate new trace ID
        trace_id = generate_trace_id()
        assert len(trace_id) == 12

        # Set and get trace ID
        set_trace_id("custom-trace")
        assert get_trace_id() == "custom-trace"

    def test_cost_tracking(self):
        """Test token and cost tracking."""
        from agentcy.observability import TokenUsage, CostTracker

        tracker = CostTracker()

        # Add usage for research
        tracker.add_usage(
            "research",
            TokenUsage(prompt_tokens=1000, completion_tokens=500, total_tokens=1500),
        )

        # Add usage for strategy
        tracker.add_usage(
            "strategy",
            TokenUsage(prompt_tokens=800, completion_tokens=400, total_tokens=1200),
        )

        summary = tracker.get_summary()
        assert summary["total_tokens"] == 2700
        assert summary["total_cost_usd"] > 0
        assert "research" in summary["by_stage"]
        assert "strategy" in summary["by_stage"]


class TestCulture:
    """Test Agno Culture integration."""

    def test_culture_seeding(self):
        """Test Culture seeding functions."""
        import tempfile
        from agentcy.culture.seed import (
            get_culture_manager,
            seed_marketing_frameworks,
            seed_quality_rubrics,
            seed_copywriting_principles,
            seed_brand_voice,
            seed_all,
            _seeded,
        )
        from agentcy.models.brand import BrandKit, VoiceGuidelines
        from agentcy.db import reset_db

        # Reset for fresh test
        reset_db()
        _seeded.clear()

        # Get culture manager
        manager = get_culture_manager()
        assert manager is not None

        # Seed marketing frameworks
        seed_marketing_frameworks(manager)
        assert "marketing_frameworks" in _seeded

        # Seed quality rubrics
        seed_quality_rubrics(manager)
        assert "quality_rubrics" in _seeded

        # Seed copywriting principles
        seed_copywriting_principles(manager)
        assert "copywriting_principles" in _seeded

        # Seed brand voice
        brand = BrandKit(
            name="TestBrand",
            voice=VoiceGuidelines(
                tone=["professional", "confident"],
                avoid=["jargon", "buzzwords"],
            ),
        )
        seed_brand_voice(manager, brand)
        assert "brand_voice:TestBrand" in _seeded

        # Clean up
        reset_db()
        _seeded.clear()

    def test_ensure_culture_seeded_convenience(self):
        """Test convenience function for seeding."""
        from agentcy.culture import ensure_culture_seeded
        from agentcy.culture.seed import _seeded
        from agentcy.db import reset_db

        # Reset for fresh test
        reset_db()
        _seeded.clear()

        # Call convenience function
        ensure_culture_seeded(brand=None)

        # Verify seeded
        assert "marketing_frameworks" in _seeded
        assert "quality_rubrics" in _seeded
        assert "copywriting_principles" in _seeded

        # Clean up
        reset_db()
        _seeded.clear()

    def test_controller_seeds_culture(self):
        """Test that CampaignController seeds Culture on init."""
        from agentcy.controller import CampaignController
        from agentcy.config import AgentcyConfig
        from agentcy.culture.seed import _seeded
        from agentcy.db import reset_db

        # Reset for fresh test
        reset_db()
        _seeded.clear()

        # Create controller (should seed Culture)
        campaign = Campaign(id="culture-test", brief="Test Culture")
        config = AgentcyConfig()
        controller = CampaignController(campaign=campaign, config=config)

        # Verify Culture was seeded
        assert "marketing_frameworks" in _seeded
        assert "quality_rubrics" in _seeded
        assert "copywriting_principles" in _seeded

        # Verify db is available
        assert controller.db is not None

        # Clean up
        reset_db()
        _seeded.clear()
