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
async def test_get_twin_includes_personalization_section() -> None:
    tenant_id = uuid4()
    student_id = uuid4()
    twin = PreparationTwin(
        id=uuid4(),
        tenant_id=tenant_id,
        student_id=student_id,
        exam_id="neet",
        profile_version=TWIN_PROFILE_V1,
        readiness_score=Decimal("70"),
        average_mastery=Decimal("70"),
        average_retention=Decimal("70"),
        average_confidence=Decimal("70"),
        rated_node_count=1,
        due_revision_count=0,
        high_risk_concept_count=0,
        largest_positive_driver=None,
        largest_negative_driver=None,
        recommendation_count=0,
        last_recommendation_at=None,
        twin_payload={
            "personalization": {
                "version": "personalization_v1",
                "learning_style": "RECOVERY_DRIVEN",
                "risk_profile": "MEDIUM_RISK",
                "top_multiplier": 1.30,
                "best_activity_type": "WEAKNESS_RECOVERY",
                "historical_effectiveness": 72.4,
            }
        },
        generated_at=datetime.now(UTC),
        best_activity_type="WEAKNESS_RECOVERY",
        top_multiplier=Decimal("1.30"),
        historical_effectiveness=Decimal("72.4"),
    )

    class _Repo:
        async def get_projection(self, *_args: object, **_kwargs: object) -> PreparationTwin:
            return twin

        async def get_projection_for_student(self, *_args: object, **_kwargs: object) -> PreparationTwin:
            return twin

    service = TwinReadService(projection_repo=_Repo())  # type: ignore[arg-type]
    response = await service.get_twin(
        tenant_id=tenant_id,
        student_id=student_id,
        exam_id="neet",
    )
    assert isinstance(response, TwinResponse)
    assert response.personalization is not None
    assert response.personalization["best_activity_type"] == "WEAKNESS_RECOVERY"


@pytest.mark.asyncio
async def test_get_dashboard_includes_personalization_fields() -> None:
    tenant_id = uuid4()
    student_id = uuid4()
    twin = PreparationTwin(
        id=uuid4(),
        tenant_id=tenant_id,
        student_id=student_id,
        exam_id="neet",
        profile_version=TWIN_PROFILE_V1,
        readiness_score=Decimal("70"),
        average_mastery=Decimal("70"),
        average_retention=Decimal("70"),
        average_confidence=Decimal("70"),
        rated_node_count=1,
        due_revision_count=0,
        high_risk_concept_count=0,
        largest_positive_driver=None,
        largest_negative_driver=None,
        recommendation_count=0,
        last_recommendation_at=None,
        twin_payload={},
        generated_at=datetime.now(UTC),
        best_activity_type="WEAKNESS_RECOVERY",
        top_multiplier=Decimal("1.30"),
    )

    class _Repo:
        async def get_projection(self, *_args: object, **_kwargs: object) -> PreparationTwin:
            return twin

        async def get_projection_for_student(self, *_args: object, **_kwargs: object) -> PreparationTwin:
            return twin

    service = TwinReadService(projection_repo=_Repo())  # type: ignore[arg-type]
    response = await service.get_dashboard(
        tenant_id=tenant_id,
        student_id=student_id,
        exam_id="neet",
    )
    assert isinstance(response, TwinDashboardResponse)
    assert response.best_activity_type == "WEAKNESS_RECOVERY"
    assert response.top_multiplier == Decimal("1.30")
