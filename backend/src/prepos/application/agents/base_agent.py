from __future__ import annotations

from prepos.application.agents.models import AgentContext
from prepos.application.agents.models import AgentResult


class BaseAgent:
    agent_type: str = "base"

    async def run(self, *, context: AgentContext, objective: str) -> AgentResult:
        raise NotImplementedError
