"""Tests for Agno agents.

Tests agent creation and tool stub functionality.
Does not require API keys - uses stub tools.
"""

import pytest

from agentcy.agents import (
    QualityReview,
    VisualConcept,
    create_copywriter,
    create_critic,
    create_marketer,
    create_researcher,
    create_strategist,
    create_visual_agent,
)
from agentcy.models.brand import BrandKit
from agentcy.tools.research import search_web, scrape_url
from agentcy.tools.visual import generate_image


class TestAgentCreation:
    """Test that agents can be created with proper configuration."""

    def test_create_researcher(self):
        agent = create_researcher(campaign_id="test-123")
        assert agent.name == "Researcher"
        assert len(agent.tools) == 2  # search_web, scrape_url

    def test_create_strategist(self):
        agent = create_strategist(campaign_id="test-123")
        assert agent.name == "Strategist"

    def test_create_copywriter_without_brand(self):
        agent = create_copywriter(campaign_id="test-123")
        assert agent.name == "Copywriter"

    def test_create_copywriter_with_brand(self):
        brand = BrandKit(
            name="Test Brand",
            tagline="Test tagline",
            voice={"tone": ["professional"], "avoid": ["jargon"]},
        )
        agent = create_copywriter(campaign_id="test-123", brand=brand)
        assert agent.name == "Copywriter"
        # Brand instructions should be included
        instructions = " ".join(agent.instructions)
        assert "professional" in instructions

    def test_create_visual_agent(self):
        agent = create_visual_agent(campaign_id="test-123")
        assert agent.name == "Visual Director"
        assert len(agent.tools) == 1  # generate_image

    def test_create_marketer(self):
        agent = create_marketer(campaign_id="test-123")
        assert agent.name == "Marketer"

    def test_create_critic(self):
        agent = create_critic()
        assert agent.name == "Critic"


class TestStubTools:
    """Test that stub tools work correctly."""

    def test_search_web_stub(self):
        results = search_web("test query", num_results=3)
        assert len(results) == 3
        assert all("title" in r for r in results)
        assert all("url" in r for r in results)
        assert all("snippet" in r for r in results)

    def test_scrape_url_stub(self):
        content = scrape_url("https://example.com")
        assert "[STUB CONTENT]" in content
        assert "https://example.com" in content

    def test_generate_image_stub(self):
        url = generate_image("test prompt")
        assert url.startswith("https://placehold.co/")
        assert "1920x1080" in url  # Default 16:9

    def test_generate_image_aspect_ratio(self):
        url = generate_image("test", aspect_ratio="1:1")
        assert "1024x1024" in url
