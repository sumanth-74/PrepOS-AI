from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from decimal import Decimal

import pytest

from prepos.application.twin.twin_dto import TwinDashboardResponse, TwinResponse
from prepos.application.twin.twin_read_service import TwinReadService
from prepos.domain.twin.profile_versions import TWIN_PROFILE_V1
from prepos.domain.twin.snapshot_entities import PreparationTwin


@pytest.mark.asyncio
async def test_get_twin_includes_mentor_section() -> None:
    tenant_id = uuid4()
    student_id = uuid4()
    twin = PreparationTwin(
        id=uuid4(),
        tenant_id=tenant_id,
        student_id=student_id,
        exam_id="neet",
        profile_version=TWIN_PROFILE_V1,
        readiness_score=None,
        average_mastery=None,
        average_retention=None,
        average_confidence=None,
        rated_node_count=0,
        due_revision_count=0,
        high_risk_concept_count=0,
        largest_positive_driver=None,
        largest_negative_driver=None,
        recommendation_count=0,
        last_recommendation_at=None,
        twin_payload={
            "mentor": {
                "version": "mentor_v1",
                "summary": {
                    "overall_status": "GOOD",
                    "key_message": "Your preparation is progressing well.",
                    "strongest_signal": "consistency",
                    "weakest_signal": "coverage",
                },
                "insights": [],
                "recommendations": [],
            }
        },
        generated_at=datetime.now(UTC),
        mentor_status="GOOD",
        top_mentor_message="Your preparation is progressing well.",
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
    assert response.mentor is not None
    assert response.mentor["summary"]["overall_status"] == "GOOD"


@pytest.mark.asyncio
async def test_get_dashboard_includes_mentor_fields() -> None:
    tenant_id = uuid4()
    student_id = uuid4()
    twin = PreparationTwin(
        id=uuid4(),
        tenant_id=tenant_id,
        student_id=student_id,
        exam_id="neet",
        profile_version=TWIN_PROFILE_V1,
        readiness_score=None,
        average_mastery=None,
        average_retention=None,
        average_confidence=None,
        rated_node_count=0,
        due_revision_count=0,
        high_risk_concept_count=0,
        largest_positive_driver=None,
        largest_negative_driver=None,
        recommendation_count=0,
        last_recommendation_at=None,
        twin_payload={},
        generated_at=datetime.now(UTC),
        mentor_status="AT_RISK",
        top_mentor_message="Your goal is at risk unless you adjust study priorities soon.",
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
    assert response.mentor_status == "AT_RISK"
    assert response.top_mentor_message == (
        "Your goal is at risk unless you adjust study priorities soon."
    )


@pytest.mark.asyncio
async def test_get_dashboard_includes_mentor_action_fields() -> None:
    tenant_id = uuid4()
    student_id = uuid4()
    twin = PreparationTwin(
        id=uuid4(),
        tenant_id=tenant_id,
        student_id=student_id,
        exam_id="neet",
        profile_version=TWIN_PROFILE_V1,
        readiness_score=None,
        average_mastery=None,
        average_retention=None,
        average_confidence=None,
        rated_node_count=0,
        due_revision_count=0,
        high_risk_concept_count=0,
        largest_positive_driver=None,
        largest_negative_driver=None,
        recommendation_count=0,
        last_recommendation_at=None,
        twin_payload={},
        generated_at=datetime.now(UTC),
        mentor_action_type="CONTACT_STUDENT",
        mentor_action_priority=Decimal("82.50"),
        escalation_level="HIGH",
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
    assert response.mentor_action == "CONTACT_STUDENT"
    assert response.mentor_action_priority == Decimal("82.50")
    assert response.escalation_level == "HIGH"


@pytest.mark.asyncio
async def test_get_twin_includes_mentor_action_and_escalation() -> None:
    tenant_id = uuid4()
    student_id = uuid4()
    twin = PreparationTwin(
        id=uuid4(),
        tenant_id=tenant_id,
        student_id=student_id,
        exam_id="neet",
        profile_version=TWIN_PROFILE_V1,
        readiness_score=None,
        average_mastery=None,
        average_retention=None,
        average_confidence=None,
        rated_node_count=0,
        due_revision_count=0,
        high_risk_concept_count=0,
        largest_positive_driver=None,
        largest_negative_driver=None,
        recommendation_count=0,
        last_recommendation_at=None,
        twin_payload={
            "mentor": {
                "mentor_action": {
                    "action_type": "CONTACT_STUDENT",
                    "priority_score": 82.5,
                    "urgency": "HIGH",
                    "expected_impact": 5.2,
                    "explanation": "Student should be contacted due to declining consistency.",
                },
                "escalation": {
                    "level": "HIGH",
                    "reason": "Escalation triggered because goal probability dropped below 50%.",
                },
            }
        },
        generated_at=datetime.now(UTC),
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
    assert response.mentor_action is not None
    assert response.mentor_action["action_type"] == "CONTACT_STUDENT"
    assert response.escalation is not None
    assert response.escalation["level"] == "HIGH"
