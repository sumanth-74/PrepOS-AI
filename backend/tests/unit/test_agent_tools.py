from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from prepos.application.agents.agent_memory_context import AgentMemoryContextBuilder
from prepos.application.agents.models import AgentContext
from prepos.application.agents.tools.forecasting_tool import ForecastingTool
from prepos.application.agents.tools.recommendation_tool import RecommendationTool
from prepos.application.memory.memory_context import MemoryContext
from prepos.application.memory.memory_models import MilestoneListResponse, MemoryRecordResponse


@pytest.mark.asyncio
async def test_forecasting_tool_requires_student_for_non_admin_persona() -> None:
    service = AsyncMock()
    tool = ForecastingTool(service=service)
    result = await tool.execute(
        context=AgentContext(
            tenant_id=uuid4(),
            user_id=uuid4(),
            persona="student",
            question="forecast",
        )
    )
    assert result.success is False
    service.get_current_forecast.assert_not_awaited()


@pytest.mark.asyncio
async def test_forecasting_tool_loads_student_forecast() -> None:
    tenant_id = uuid4()
    user_id = uuid4()
    student_id = uuid4()

    class FakeForecast:
        def model_dump(self, *, mode: str = "python") -> dict[str, float]:
            return {"probability_of_success": 68.0}

    service = AsyncMock()
    service.get_current_forecast.return_value = FakeForecast()

    tool = ForecastingTool(service=service)
    result = await tool.execute(
        context=AgentContext(
            tenant_id=tenant_id,
            user_id=user_id,
            persona="student",
            question="forecast",
            student_id=student_id,
            student_user_id=user_id,
            exam_id="upsc_cse",
        )
    )

    assert result.success is True
    assert result.data["probability_of_success"] == 68.0
    service.get_current_forecast.assert_awaited_once_with(
        tenant_id=tenant_id,
        user_id=user_id,
        exam_id="upsc_cse",
    )


@pytest.mark.asyncio
async def test_recommendation_tool_delegates_to_service() -> None:
    tenant_id = uuid4()
    user_id = uuid4()
    student_id = uuid4()

    class FakeRecommendations:
        def model_dump(self, *, mode: str = "python") -> dict[str, list[dict[str, str]]]:
            return {"recommendations": [{"concept_name": "Federalism", "concept_id": "fed_1"}]}

    service = AsyncMock()
    service.get_student_recommendations = AsyncMock(return_value=FakeRecommendations())

    tool = RecommendationTool(service=service)
    result = await tool.execute(
        context=AgentContext(
            tenant_id=tenant_id,
            user_id=user_id,
            persona="student",
            question="what should I study next",
            student_id=student_id,
            student_user_id=user_id,
            exam_id="upsc_cse",
        )
    )

    assert result.success is True
    assert result.data["recommendations"][0]["concept_name"] == "Federalism"


@pytest.mark.asyncio
async def test_agent_memory_context_builder_loads_student_context() -> None:
    tenant_id = uuid4()
    user_id = uuid4()
    memory_service = AsyncMock()
    memory_service.load_student_context.return_value = MemoryContext(context_lines=["Milestone reached"])
    milestone = MemoryRecordResponse(
        id=uuid4(),
        tenant_id=tenant_id,
        user_id=user_id,
        persona="student",
        memory_type="progress_milestones",
        memory_key="pyq_block_3",
        memory_value={"title": "Completed PYQ block"},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    memory_service.get_milestones.return_value = MilestoneListResponse(milestones=[milestone], total=1)

    builder = AgentMemoryContextBuilder(memory_service=memory_service)
    context = await builder.build(
        tenant_id=tenant_id,
        user_id=user_id,
        persona="student",
    )

    assert context["context_lines"] == ["Milestone reached"]
    assert context["milestones"][0]["memory_value"]["title"] == "Completed PYQ block"
