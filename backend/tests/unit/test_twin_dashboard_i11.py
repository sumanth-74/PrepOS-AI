from __future__ import annotations

from datetime import UTC, datetime, date
from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from prepos.application.twin.twin_read_service import TwinReadService
from prepos.domain.twin.profile_versions import TWIN_PROFILE_V1
from prepos.domain.twin.snapshot_entities import PreparationTwin


@pytest.mark.asyncio
async def test_dashboard_exposes_goal_mentor_case_and_effectiveness() -> None:
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
        largest_positive_driver="knowledge",
        largest_negative_driver="coverage",
        recommendation_count=5,
        last_recommendation_at=now,
        twin_payload={
            "goal": {
                "target_readiness_score": 85.0,
                "target_date": "2026-12-31",
            },
            "mentor": {
                "mentor_case": {
                    "case_status": "OPEN",
                    "priority": "HIGH",
                    "opened_at": now.isoformat(),
                },
                "mentor_effectiveness": {
                    "best_action": "CONTACT_STUDENT",
                    "effectiveness_score": 84.2,
                    "sample_size": 42,
                },
            },
        },
        generated_at=now,
        active_case_status="OPEN",
        active_case_priority="HIGH",
    )

    class _Repo:
        async def get_projection(
            self,
            tenant_id_arg: object,
            student_id_arg: object,
            exam_id: str,
        ) -> PreparationTwin:
            return twin

        async def get_projection_for_student(
            self,
            tenant_id_arg: object,
            student_id_arg: object,
        ) -> PreparationTwin:
            return twin

    service = TwinReadService(projection_repo=_Repo())  # type: ignore[arg-type]
    dashboard = await service.get_dashboard(
        tenant_id=tenant_id,
        student_id=student_id,
        exam_id="neet",
    )
    assert dashboard.goal_summary is not None
    assert dashboard.goal_summary.target_readiness_score == Decimal("85.0")
    assert dashboard.goal_summary.target_date == date(2026, 12, 31)
    assert dashboard.mentor_case is not None
    assert dashboard.mentor_case.case_status == "OPEN"
    assert dashboard.mentor_effectiveness is not None
    assert dashboard.mentor_effectiveness.best_action == "CONTACT_STUDENT"
    assert dashboard.mentor_effectiveness.effectiveness_score == Decimal("84.2")
    assert dashboard.mentor_effectiveness.sample_size == 42
