from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from prepos.application.mentor.mentor_case_read_service import MentorCaseReadService
from prepos.domain.mentor.mentor_case_entities import MentorCaseDashboardMetrics
from prepos.domain.mentor.mentor_effectiveness_learning_v1 import (
    MentorActionEffectiveness,
    MentorEffectivenessLearningResult,
)
from prepos.domain.mentor.mentor_types_v1 import MentorActionType


@pytest.mark.asyncio
async def test_get_dashboard_returns_metrics() -> None:
    tenant_id = uuid4()

    class _Repo:
        async def get_dashboard_metrics(
            self,
            tenant_id_arg: UUID,
        ) -> MentorCaseDashboardMetrics:
            assert tenant_id_arg == tenant_id
            return MentorCaseDashboardMetrics(
                open_cases=5,
                critical_cases=2,
                average_resolution_time_hours=Decimal("12.50"),
                mentor_effectiveness_score=Decimal("74.00"),
            )

    service = MentorCaseReadService(case_repo=_Repo())  # type: ignore[arg-type]
    response = await service.get_dashboard(tenant_id=tenant_id)
    assert response.open_cases == 5
    assert response.critical_cases == 2
    assert response.average_resolution_time_hours == Decimal("12.50")
    assert response.mentor_effectiveness_score == Decimal("74.00")
    assert response.best_action is None
    assert response.best_action_effectiveness == Decimal("0")
    assert response.average_action_effectiveness == Decimal("0")


@pytest.mark.asyncio
async def test_get_dashboard_includes_learning_summary() -> None:
    tenant_id = uuid4()

    class _CaseRepo:
        async def get_dashboard_metrics(
            self,
            tenant_id_arg: UUID,
        ) -> MentorCaseDashboardMetrics:
            assert tenant_id_arg == tenant_id
            return MentorCaseDashboardMetrics(
                open_cases=1,
                critical_cases=0,
                average_resolution_time_hours=Decimal("4.00"),
                mentor_effectiveness_score=Decimal("74.00"),
            )

    class _LearningRepo:
        async def get_tenant_learning_summary(
            self,
            tenant_id_arg: UUID,
        ) -> MentorEffectivenessLearningResult:
            assert tenant_id_arg == tenant_id
            return MentorEffectivenessLearningResult(
                action_effectiveness=(
                    MentorActionEffectiveness(
                        action_type=MentorActionType.CONTACT_STUDENT,
                        effectiveness_score=Decimal("84.20"),
                        readiness_delta=Decimal("5.00"),
                        predicted_score_delta=Decimal("4.00"),
                        success_rate=Decimal("80.00"),
                        sample_size=42,
                    ),
                ),
                best_action=MentorActionType.CONTACT_STUDENT,
                best_action_effectiveness=Decimal("84.20"),
                average_action_effectiveness=Decimal("84.20"),
            )

    service = MentorCaseReadService(
        case_repo=_CaseRepo(),  # type: ignore[arg-type]
        learning_repo=_LearningRepo(),  # type: ignore[arg-type]
    )
    response = await service.get_dashboard(tenant_id=tenant_id)
    assert response.best_action == "CONTACT_STUDENT"
    assert response.best_action_effectiveness == Decimal("84.20")
    assert response.average_action_effectiveness == Decimal("84.20")
