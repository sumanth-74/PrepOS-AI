from __future__ import annotations

from prepos.application.agents.agents.student_success_agent import CompositeAgent
from prepos.application.agents.registry import ToolRegistry


class CurrentAffairsAgent(CompositeAgent):
    def __init__(self, registry: ToolRegistry) -> None:
        super().__init__(
            agent_type="current_affairs_agent",
            default_tools=["current_affairs"],
            registry=registry,
        )
