from __future__ import annotations

from prepos.application.agents.agents.student_success_agent import CompositeAgent
from prepos.application.agents.registry import ToolRegistry


class ForecastingAgent(CompositeAgent):
    def __init__(self, registry: ToolRegistry) -> None:
        super().__init__(
            agent_type="forecasting_agent",
            default_tools=["forecasting"],
            registry=registry,
        )
