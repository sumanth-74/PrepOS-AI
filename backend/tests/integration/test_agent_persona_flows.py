from __future__ import annotations

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from prepos.application.agents.agents.student_success_agent import (
    InstitutionStrategyAgent,
    MentorCoachAgent,
    StudentSuccessAgent,
)
from prepos.application.agents.models import AgentContext
from prepos.application.agents.registry import ToolRegistry
from prepos.application.agents.tools.base_tool import BaseTool
from prepos.application.agents.models import AgentResult


class _NamedTool(BaseTool):
    def __init__(self, tool_name: str, payload: dict[str, object]) -> None:
        self.name = tool_name
        self._payload = payload

    async def execute(self, *, context: AgentContext) -> AgentResult:
        return self._success(
            data=self._payload,
            reasoning=f"{self.name} completed.",
            label=self.name.title(),
            reference=f"tool://{self.name}",
        )


def _registry(*tool_names: str) -> ToolRegistry:
    tools = {
        name: _NamedTool(name, {"tool": name})
        for name in tool_names
    }
    return ToolRegistry(tools)


@pytest.mark.asyncio
async def test_student_success_agent_flow() -> None:
    agent = StudentSuccessAgent(
        _registry("memory", "forecasting", "recommendation", "planning", "twin")
    )
    result = await agent.run(
        context=AgentContext(
            tenant_id=uuid4(),
            user_id=uuid4(),
            persona="student",
            question="How can I improve my readiness?",
            student_id=uuid4(),
        ),
        objective="How can I improve my readiness?",
        tool_names=["memory", "forecasting", "recommendation"],
    )

    assert result.success is True
    assert len(result.data["tool_results"]) == 3


@pytest.mark.asyncio
async def test_mentor_coach_agent_flow() -> None:
    agent = MentorCoachAgent(_registry("memory", "forecasting", "intervention", "recommendation"))
    result = await agent.run(
        context=AgentContext(
            tenant_id=uuid4(),
            user_id=uuid4(),
            persona="mentor",
            question="What should I do with this student?",
            student_id=uuid4(),
            student_user_id=uuid4(),
        ),
        objective="What should I do with this student?",
        tool_names=["memory", "forecasting", "intervention"],
    )

    assert result.success is True
    assert result.agent_type == "mentor_coach_agent"


@pytest.mark.asyncio
async def test_institution_strategy_agent_flow() -> None:
    agent = InstitutionStrategyAgent(_registry("institution", "cohort", "forecasting", "intervention"))
    result = await agent.run(
        context=AgentContext(
            tenant_id=uuid4(),
            user_id=uuid4(),
            persona="admin",
            question="What should management focus on next month?",
        ),
        objective="What should management focus on next month?",
        tool_names=["institution", "cohort"],
    )

    assert result.success is True
    assert result.agent_type == "institution_strategy_agent"
