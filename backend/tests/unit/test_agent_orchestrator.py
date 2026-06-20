from __future__ import annotations

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from prepos.application.agents.agent_memory_context import AgentMemoryContextBuilder
from prepos.application.agents.models import AgentContext, AgentResult
from prepos.application.agents.orchestrator import AgentOrchestrator
from prepos.application.agents.registry import ToolRegistry
from prepos.application.agents.tools.base_tool import BaseTool


class _StubTool(BaseTool):
    name = "forecasting"

    async def execute(self, *, context: AgentContext) -> AgentResult:
        return self._success(
            data={"probability_of_success": 72.0},
            reasoning="Stub forecast loaded.",
            label="Forecasting",
            reference="GET /forecasting/current",
        )


@pytest.mark.asyncio
async def test_orchestrator_executes_plan_and_persists_execution() -> None:
    tenant_id = uuid4()
    user_id = uuid4()
    student_id = uuid4()
    execution_id = uuid4()

    repository = AsyncMock()
    repository.save_execution.return_value = execution_id
    repository.save_critique.return_value = uuid4()
    repository.save_reflection.return_value = uuid4()
    repository.save_execution_graph = AsyncMock()

    memory_builder = AsyncMock()
    memory_builder.build.return_value = {"context_lines": ["Completed 3 milestones"], "milestones": []}

    registry = ToolRegistry({"forecasting": _StubTool()})
    orchestrator = AgentOrchestrator(
        repository=repository,
        tool_registry=registry,
        memory_builder=memory_builder,
    )

    response = await orchestrator.execute(
        tenant_id=tenant_id,
        user_id=user_id,
        persona="student",
        question="How can I improve my readiness before prelims?",
        student_id=student_id,
        student_user_id=user_id,
        exam_id="upsc_cse",
    )

    assert response.agent_used == "student_success_agent"
    assert response.execution_id == execution_id
    assert response.confidence in {"high", "medium", "low"}
    assert "coordinated" in response.answer
    repository.save_execution.assert_awaited_once()
    repository.save_critique.assert_awaited_once()
    repository.save_execution_graph.assert_awaited_once()


@pytest.mark.asyncio
async def test_orchestrator_selects_mentor_agent_for_mentor_persona() -> None:
    repository = AsyncMock()
    repository.save_execution.return_value = uuid4()
    repository.save_critique.return_value = uuid4()
    repository.save_execution_graph = AsyncMock()
    memory_builder = AsyncMock()
    memory_builder.build.return_value = {"context_lines": [], "milestones": []}

    class _MemoryTool(BaseTool):
        name = "memory"

        async def execute(self, *, context: AgentContext) -> AgentResult:
            return self._success(
                data={"context_lines": ["Mentor memory loaded"]},
                reasoning="Memory loaded.",
                label="Memory",
                reference="GET /memory",
            )

    registry = ToolRegistry({"memory": _MemoryTool()})
    orchestrator = AgentOrchestrator(
        repository=repository,
        tool_registry=registry,
        memory_builder=memory_builder,
    )

    response = await orchestrator.execute(
        tenant_id=uuid4(),
        user_id=uuid4(),
        persona="mentor",
        question="What should I do with this student?",
        student_id=uuid4(),
        student_user_id=uuid4(),
    )

    assert response.agent_used == "mentor_coach_agent"
