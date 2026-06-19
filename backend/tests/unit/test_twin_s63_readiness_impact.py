from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from prepos.application.twin.twin_read_service import TwinReadService
from prepos.domain.twin.entities import PersistedTwinRecommendation
from prepos.domain.twin.profile_versions import TWIN_PROFILE_V1
from prepos.domain.twin.recommendations_v1 import explain_recommendation
from prepos.domain.twin.snapshot_entities import PreparationTwin
from prepos.domain.twin.twin_payload_v1 import (
    TwinRecommendationsPayloadInputs,
    build_recommendations_payload_section,
)
from prepos.domain.twin.value_objects import RecommendationType


def test_explanation_includes_readiness_gain_for_revision_due() -> None:
    explanation = explain_recommendation(
        RecommendationType.REVISION_DUE,
        readiness_gain=Decimal("4.20"),
    )
    assert "4.2 points" in explanation
    assert "overdue for revision" in explanation


def test_explanation_includes_readiness_gain_for_weakness_recovery() -> None:
    explanation = explain_recommendation(
        RecommendationType.WEAKNESS_RECOVERY,
        readiness_gain=Decimal("3.80"),
    )
    assert "3.8 points" in explanation
    assert "improvement potential" in explanation


def test_build_recommendations_payload_section_includes_total_estimated_gain() -> None:
    now = datetime(2026, 6, 18, tzinfo=UTC)
    tenant_id = uuid4()
    student_id = uuid4()
    top = tuple(
        PersistedTwinRecommendation(
            id=uuid4(),
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id="neet",
            concept_id=f"concept-{index}",
            recommendation_type="WEAKNESS_RECOVERY",
            recommendation_score=Decimal("80"),
            readiness_gain=Decimal(str(3 - index * 0.5)),
            created_at=now,
        )
        for index in range(6)
    )

    section = build_recommendations_payload_section(
        TwinRecommendationsPayloadInputs(
            recommendation_count=6,
            last_recommendation_at=now,
            top_recommendations=top,
        )
    )

    assert section["total_estimated_gain"] == 10.0
    assert section["recommendation_count"] == 6
    top_items = section["top"]
    assert isinstance(top_items, list)
    assert top_items[0]["readiness_gain"] == 3.0


@pytest.mark.asyncio
async def test_dashboard_exposes_total_estimated_gain() -> None:
    now = datetime(2026, 6, 18, tzinfo=UTC)
    twin = PreparationTwin(
        id=uuid4(),
        tenant_id=uuid4(),
        student_id=uuid4(),
        exam_id="neet",
        profile_version=TWIN_PROFILE_V1,
        readiness_score=Decimal("70"),
        average_mastery=Decimal("70"),
        average_retention=Decimal("70"),
        average_confidence=Decimal("70"),
        rated_node_count=5,
        due_revision_count=1,
        high_risk_concept_count=1,
        largest_positive_driver="knowledge",
        largest_negative_driver="coverage",
        recommendation_count=3,
        last_recommendation_at=now,
        twin_payload={
            "recommendations": {
                "recommendation_count": 3,
                "total_estimated_gain": 14.6,
            }
        },
        generated_at=now,
    )

    class _Repo:
        async def get_projection_for_student(self, tenant_id, student_id):  # noqa: ANN001
            return twin

    service = TwinReadService(projection_repo=_Repo())
    dashboard = await service.get_dashboard(tenant_id=twin.tenant_id, student_id=twin.student_id)
    twin_response = await service.get_twin(tenant_id=twin.tenant_id, student_id=twin.student_id)

    assert dashboard.total_estimated_gain == Decimal("14.6")
    assert twin_response.total_estimated_gain == Decimal("14.6")
