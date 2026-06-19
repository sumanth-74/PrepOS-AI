from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest

from prepos.application.learning_graph.activity_service import LearningGraphActivityService
from prepos.domain.learning_graph.events import AssessmentCompleted


@pytest.mark.asyncio
async def test_publish_assessment_completed_enqueues_outbox_event() -> None:
    tenant_id = uuid4()
    student_id = uuid4()
    outbox = AsyncMock()
    service = LearningGraphActivityService(outbox=outbox)
    await service.publish_assessment_completed(
        tenant_id=tenant_id,
        student_id=student_id,
        exam_id="neet",
        concept_id="concept-a",
        mcq_correct=True,
        self_confidence=Decimal("4.0"),
        correlation_id="corr",
        causation_id=None,
        current_time=datetime(2026, 6, 18, tzinfo=UTC),
    )
    outbox.enqueue_assessment_completed.assert_awaited_once()
    event = outbox.enqueue_assessment_completed.await_args.args[0]
    assert isinstance(event, AssessmentCompleted)
    assert event.concept_id == "concept-a"
    assert event.mcq_correct is True
