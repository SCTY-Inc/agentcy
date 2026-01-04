"""Agno agents for campaign generation.

6 specialized agents (reduced from original 9):
    - Researcher: Web search, competitor analysis
    - Strategist: Positioning, messaging frameworks
    - Copywriter: Headlines, body copy, CTAs
    - Visual: Image generation, art direction
    - Marketer: Channel planning, content calendar
    - Critic: Quality review, brand validation
"""

from agentcy.agents.copywriter import create_copywriter, run_copywriting
from agentcy.agents.critic import QualityReview, create_critic, review_artifact
from agentcy.agents.marketer import create_marketer, run_activation_planning
from agentcy.agents.researcher import create_researcher, run_research
from agentcy.agents.strategist import create_strategist, run_strategy
from agentcy.agents.visual import VisualConcept, create_visual_agent, run_visual_creation

__all__ = [
    # Researcher
    "create_researcher",
    "run_research",
    # Strategist
    "create_strategist",
    "run_strategy",
    # Copywriter
    "create_copywriter",
    "run_copywriting",
    # Visual
    "create_visual_agent",
    "run_visual_creation",
    "VisualConcept",
    # Marketer
    "create_marketer",
    "run_activation_planning",
    # Critic
    "create_critic",
    "review_artifact",
    "QualityReview",
]
