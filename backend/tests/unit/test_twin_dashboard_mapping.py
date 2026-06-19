from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from prepos.application.twin.twin_read_service import TwinReadService
from prepos.domain.twin.profile_versions import TWIN_PROFILE_V1
from prepos.domain.twin.snapshot_entities import PreparationTwin


class InMemoryTwinProjectionRepository:
    def __init__(self, twin: PreparationTwin | None) -> None:
        self._twin = twin

    async def resolve_twin_id(self, tenant_id, student_id, exam_id):  # noqa: ANN001
        return self._twin.id if self._twin else None

    async def upsert_projection(self, twin):  # noqa: ANN001
        self._twin = twin
        return twin

    async def get_projection(self, tenant_id, student_id, exam_id):  # noqa: ANN001
        return self._twin

    async def get_projection_for_student(self, tenant_id, student_id):  # noqa: ANN001
        return self._twin


@pytest.mark.asyncio
async def test_dashboard_response_mapping() -> None:
    now = datetime(2026, 6, 18, tzinfo=UTC)
    twin = PreparationTwin(
        id=uuid4(),
        tenant_id=uuid4(),
        student_id=uuid4(),
        exam_id="neet",
        profile_version=TWIN_PROFILE_V1,
        readiness_score=Decimal("81.25"),
        average_mastery=Decimal("85.00"),
        average_retention=Decimal("78.00"),
        average_confidence=Decimal("80.00"),
        rated_node_count=10,
        due_revision_count=4,
        high_risk_concept_count=2,
        largest_positive_driver="knowledge",
        largest_negative_driver="coverage",
        recommendation_count=5,
        last_recommendation_at=now,
        twin_payload={
            "drivers": {
                "top_positive_drivers": ["knowledge", "confidence"],
                "top_negative_drivers": ["coverage", "retention"],
            }
        },
        generated_at=now,
    )
    service = TwinReadService(projection_repo=InMemoryTwinProjectionRepository(twin))

    dashboard = await service.get_dashboard(
        tenant_id=twin.tenant_id,
        student_id=twin.student_id,
    )

    assert dashboard.readiness_score == Decimal("81.25")
    assert dashboard.due_revision_count == 4
    assert dashboard.high_risk_concept_count == 2
    assert dashboard.recommendation_count == 5
    assert dashboard.largest_positive_driver == "knowledge"
    assert dashboard.largest_negative_driver == "coverage"
    assert dashboard.top_positive_drivers == ["knowledge", "confidence"]
    assert dashboard.top_negative_drivers == ["coverage", "retention"]
    assert dashboard.generated_at == now
