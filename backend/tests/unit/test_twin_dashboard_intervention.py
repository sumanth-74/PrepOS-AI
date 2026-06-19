from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from prepos.application.twin.twin_dto import TwinDashboardResponse, TwinResponse
from prepos.application.twin.twin_read_service import TwinReadService
from prepos.domain.twin.profile_versions import TWIN_PROFILE_V1
from prepos.domain.twin.snapshot_entities import PreparationTwin


@pytest.mark.asyncio
async def test_dashboard_exposes_intervention_metrics() -> None:
    now = datetime(2026, 6, 18, tzinfo=UTC)
    tenant_id = uuid4()
    student_id = uuid4()
    twin = PreparationTwin(
        id=uuid4(),
        tenant_id=tenant_id,
        student_id=student_id,
        exam_id="neet",
        profile_version=TWIN_PROFILE_V1,
        readiness_score=Decimal("71.5"),
        average_mastery=Decimal("60"),
        average_retention=Decimal("55"),
        average_confidence=Decimal("65"),
        rated_node_count=10,
        due_revision_count=2,
        high_risk_concept_count=1,
        largest_positive_driver="mastery",
        largest_negative_driver="retention",
        recommendation_count=5,
        last_recommendation_at=now,
        twin_payload={
            "intervention": {
                "intervention_type": "REVISION_SPRINT",
                "intervention_score": 88.5,
                "urgency": "HIGH",
                "expected_readiness_gain": 4.2,
                "title": "Complete 2 overdue revision sprint",
                "description": "Clear overdue revision items before adding new study topics to stabilize retention.",
            }
        },
        generated_at=now,
        projection_revision=1,
        rebuild_count=0,
        skipped_rebuild_count=0,
        incremental_update_count=0,
        lock_contention_count=0,
        intervention_type="REVISION_SPRINT",
        intervention_score=Decimal("88.5"),
        intervention_urgency="HIGH",
    )

    class _Repo:
        async def get_projection(
            self,
            tenant_id: object,
            student_id: object,
            exam_id: str,
        ) -> PreparationTwin:
            return twin

        async def get_projection_for_student(
            self,
            tenant_id: object,
            student_id: object,
        ) -> PreparationTwin:
            return twin

    service = TwinReadService(projection_repo=_Repo())  # type: ignore[arg-type]
    dashboard = await service.get_dashboard(
        tenant_id=tenant_id,
        student_id=student_id,
        exam_id="neet",
    )
    twin_response = await service.get_twin(
        tenant_id=tenant_id,
        student_id=student_id,
        exam_id="neet",
    )

    assert isinstance(dashboard, TwinDashboardResponse)
    assert dashboard.current_intervention == "REVISION_SPRINT"
    assert dashboard.intervention_urgency == "HIGH"
    assert dashboard.intervention_score == Decimal("88.5")
    assert isinstance(twin_response, TwinResponse)
    assert twin_response.intervention is not None
    assert twin_response.intervention["intervention_type"] == "REVISION_SPRINT"
