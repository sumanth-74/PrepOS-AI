from __future__ import annotations

from prepos.application.agents.agents.student_success_agent import CompositeAgent
from prepos.application.agents.registry import ToolRegistry


class RecommendationAgent(CompositeAgent):
    def __init__(self, registry: ToolRegistry) -> None:
        super().__init__(
            agent_type="recommendation_agent",
            default_tools=["recommendation"],
            registry=registry,
        )
