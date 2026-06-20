from __future__ import annotations

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from prepos.application.agents.event_dispatcher import AgentEventDispatcher, AgentEventPayload
from prepos.application.agents.events.workflows import WeakConceptEmergenceWorkflow


@pytest.mark.asyncio
async def test_event_dispatcher_generates_autonomous_actions() -> None:
    repository = AsyncMock()
    repository.save_workflow.return_value = uuid4()
    repository.record_workflow_event.return_value = uuid4()
    dispatcher = AgentEventDispatcher(
        repository=repository,
        autonomous_service=AsyncMock(),
    )
    dispatcher._autonomous.execute_actions = AsyncMock(side_effect=lambda **kwargs: kwargs["actions"])

    actions = await dispatcher.dispatch(
        tenant_id=uuid4(),
        event=AgentEventPayload(
            event_type="weak_concept_emergence",
            subject_key="student_1",
            metadata={"concept_id": "federalism", "weakness_score": 8.5},
        ),
    )
    assert actions
    assert any(action.action_type == "recommendation" for action in actions)


@pytest.mark.asyncio
async def test_weak_concept_emergence_workflow() -> None:
    repository = AsyncMock()
    repository.save_workflow.return_value = uuid4()
    workflow = WeakConceptEmergenceWorkflow()
    notification = await workflow.run(
        repository=repository,
        tenant_id=uuid4(),
        subject_key="student_2",
        concept_id="polity",
        weakness_score=7.0,
    )
    assert "polity" in notification.message
