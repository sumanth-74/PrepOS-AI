from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from prepos.application.twin.twin_dto import TwinDashboardResponse, TwinResponse
from prepos.application.twin.twin_read_service import TwinReadService
from prepos.domain.twin.profile_versions import TWIN_PROFILE_V1
from prepos.domain.twin.snapshot_entities import PreparationTwin


def _build_twin(*, twin_payload: dict[str, object]) -> PreparationTwin:
    now = datetime(2026, 6, 18, tzinfo=UTC)
    return PreparationTwin(
        id=uuid4(),
        tenant_id=uuid4(),
        student_id=uuid4(),
        exam_id="neet",
        profile_version=TWIN_PROFILE_V1,
        readiness_score=Decimal("74.5"),
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
        twin_payload=twin_payload,
        generated_at=now,
        projection_revision=1,
        rebuild_count=0,
        skipped_rebuild_count=0,
        incremental_update_count=0,
        lock_contention_count=0,
    )


class _Repo:
    def __init__(self, twin: PreparationTwin) -> None:
        self._twin = twin

    async def get_projection(
        self,
        tenant_id: object,
        student_id: object,
        exam_id: str,
    ) -> PreparationTwin:
        return self._twin

    async def get_projection_for_student(
        self,
        tenant_id: object,
        student_id: object,
    ) -> PreparationTwin:
        return self._twin


@pytest.mark.asyncio
async def test_dashboard_exposes_predicted_score_metrics() -> None:
    twin = _build_twin(
        twin_payload={
            "predicted_outcome": {
                "version": "predicted_score_v1",
                "expected_score": 74.5,
                "low_score": 68.2,
                "high_score": 80.8,
                "risk_level": "MEDIUM",
            }
        }
    )
    service = TwinReadService(projection_repo=_Repo(twin))  # type: ignore[arg-type]
    dashboard = await service.get_dashboard(
        tenant_id=twin.tenant_id,
        student_id=twin.student_id,
        exam_id="neet",
    )

    assert isinstance(dashboard, TwinDashboardResponse)
    assert dashboard.expected_score == Decimal("74.5")
    assert dashboard.low_score == Decimal("68.2")
    assert dashboard.high_score == Decimal("80.8")
    assert dashboard.risk_level == "MEDIUM"


@pytest.mark.asyncio
async def test_twin_api_exposes_predicted_outcome_and_simulations() -> None:
    twin = _build_twin(
        twin_payload={
            "predicted_outcome": {
                "version": "predicted_score_v1",
                "expected_score": 74.5,
                "low_score": 68.2,
                "high_score": 80.8,
                "risk_level": "MEDIUM",
            },
            "simulations": {
                "current_state": 74.5,
                "complete_recommendations": 82.0,
                "no_study": 66.0,
            },
        }
    )
    service = TwinReadService(projection_repo=_Repo(twin))  # type: ignore[arg-type]
    response = await service.get_twin(
        tenant_id=twin.tenant_id,
        student_id=twin.student_id,
        exam_id="neet",
    )

    assert isinstance(response, TwinResponse)
    assert response.predicted_outcome is not None
    assert response.predicted_outcome["expected_score"] == 74.5
    assert response.simulations is not None
    assert response.simulations["complete_recommendations"] == 82.0
