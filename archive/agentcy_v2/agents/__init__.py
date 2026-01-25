"""Campaign generation agents.

6 specialized agents using direct Gemini SDK:
    - Researcher: Web search, competitor analysis
    - Strategist: Positioning, messaging frameworks
    - Copywriter: Headlines, body copy, CTAs
    - Visual: Image generation, art direction
    - Marketer: Channel planning, content calendar
    - Critic: Quality review, brand validation
"""

from agentcy.agents.copywriter import run_copywriting
from agentcy.agents.critic import QualityReview, review_artifact
from agentcy.agents.marketer import run_activation_planning
from agentcy.agents.researcher import run_research
from agentcy.agents.strategist import run_strategy
from agentcy.agents.visual import VisualConcept, run_visual_creation

__all__ = [
    # Researcher
    "run_research",
    # Strategist
    "run_strategy",
    # Copywriter
    "run_copywriting",
    # Visual
    "run_visual_creation",
    "VisualConcept",
    # Marketer
    "run_activation_planning",
    # Critic
    "review_artifact",
    "QualityReview",
]
