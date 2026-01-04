"""Smoke test to verify dependency compatibility."""

import pytest


def test_agentcy_imports():
    """Verify agentcy package imports without error."""
    import agentcy
    assert agentcy.__version__ == "2.0.0-alpha"


def test_models_import():
    """Verify models subpackage imports."""
    from agentcy.models import Stage
    from agentcy.models.stages import STAGE_ORDER
    assert Stage.INTAKE in STAGE_ORDER


def test_pydantic_models():
    """Verify Pydantic schemas are valid."""
    from agentcy.models.artifacts import ResearchReport, StrategyBrief
    from agentcy.models.brand import BrandKit
    from agentcy.models.campaign import Campaign

    # Should not raise
    brand = BrandKit(name="Test Brand")
    assert brand.name == "Test Brand"
