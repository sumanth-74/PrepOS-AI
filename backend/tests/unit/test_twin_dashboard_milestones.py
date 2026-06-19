from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from prepos.application.twin.twin_dto import TwinDashboardResponse
from prepos.application.twin.twin_read_service import TwinReadService
from prepos.domain.twin.profile_versions import TWIN_PROFILE_V1
from prepos.domain.twin.snapshot_entities import PreparationTwin


@pytest.mark.asyncio
async def test_dashboard_exposes_milestone_metrics() -> None:
    now = datetime(2026, 6, 18, tzinfo=UTC)
    tenant_id = uuid4()
    student_id = uuid4()
    twin = PreparationTwin(
        id=uuid4(),
        tenant_id=tenant_id,
        student_id=student_id,
        exam_id="neet",
        profile_version=TWIN_PROFILE_V1,
        readiness_score=Decimal("58"),
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
            "trajectory": {
                "required_gain": 14.5,
                "expected_daily_progress": 0.24,
                "expected_weekly_progress": 1.68,
            },
            "milestones": [
                {
                    "target_date": "2026-06-25",
                    "target_readiness": 62.92,
                    "expected_score": 60.0,
                },
                {
                    "target_date": "2026-07-02",
                    "target_readiness": 65.83,
                    "expected_score": 62.0,
                },
            ],
            "milestone_status": {
                "status": "BEHIND",
                "current_gap": 4.92,
            },
        },
        generated_at=now,
        projection_revision=1,
        rebuild_count=0,
        skipped_rebuild_count=0,
        incremental_update_count=0,
        lock_contention_count=0,
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

    assert isinstance(dashboard, TwinDashboardResponse)
    assert dashboard.milestone_status == "BEHIND"
    assert dashboard.expected_weekly_progress == Decimal("1.68")
    assert dashboard.next_milestone_date == date(2026, 6, 25)
    assert dashboard.next_milestone_target == Decimal("62.92")
