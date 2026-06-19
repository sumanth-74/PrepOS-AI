from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from prepos.application.mentor.mentor_case_mapper import map_case_response
from prepos.application.mentor.mentor_case_ports import MentorCaseRepositoryPort
from prepos.application.mentor.mentor_dto import (
    MentorCaseResponse,
    MentorDashboardResponse,
    MentorQueueItemResponse,
    MentorQueueResponse,
)
from prepos.application.mentor.mentor_effectiveness_learning_ports import (
    MentorEffectivenessLearningRepositoryPort,
)
from prepos.core.exceptions import DomainError
from prepos.domain.mentor.mentor_types_v1 import CaseStatus


class MentorCaseReadService:
    def __init__(
        self,
        *,
        case_repo: MentorCaseRepositoryPort,
        learning_repo: MentorEffectivenessLearningRepositoryPort | None = None,
    ) -> None:
        self._case_repo = case_repo
        self._learning_repo = learning_repo

    async def get_case(
        self,
        *,
        tenant_id: UUID,
        case_id: UUID,
    ) -> MentorCaseResponse:
        case = await self._case_repo.get_case(tenant_id, case_id)
        if case is None:
            raise DomainError("Mentor case not found.", details={"case_id": str(case_id)})
        notes = await self._case_repo.list_notes(tenant_id, case_id)
        return map_case_response(case, notes=notes)

    async def list_cases(
        self,
        *,
        tenant_id: UUID,
        status: CaseStatus | None = None,
        limit: int = 100,
    ) -> list[MentorCaseResponse]:
        cases = await self._case_repo.list_cases(
            tenant_id,
            status=status,
            limit=limit,
        )
        return [map_case_response(case) for case in cases]

    async def get_dashboard(
        self,
        *,
        tenant_id: UUID,
    ) -> MentorDashboardResponse:
        metrics = await self._case_repo.get_dashboard_metrics(tenant_id)
        best_action: str | None = None
        best_action_effectiveness = Decimal("0")
        average_action_effectiveness = Decimal("0")
        if self._learning_repo is not None:
            summary = await self._learning_repo.get_tenant_learning_summary(tenant_id)
            if summary.best_action is not None:
                best_action = summary.best_action.value
            best_action_effectiveness = summary.best_action_effectiveness
            average_action_effectiveness = summary.average_action_effectiveness
        return MentorDashboardResponse(
            open_cases=metrics.open_cases,
            critical_cases=metrics.critical_cases,
            average_resolution_time_hours=metrics.average_resolution_time_hours,
            mentor_effectiveness_score=metrics.mentor_effectiveness_score,
            best_action=best_action,
            best_action_effectiveness=best_action_effectiveness,
            average_action_effectiveness=average_action_effectiveness,
        )


class MentorQueueReadService:
    def __init__(self, *, case_repo: MentorCaseRepositoryPort) -> None:
        self._case_repo = case_repo

    async def list_queue(
        self,
        *,
        tenant_id: UUID,
        limit: int = 50,
    ) -> MentorQueueResponse:
        entries = await self._case_repo.list_queue(tenant_id, limit=limit)
        items = [
            MentorQueueItemResponse(
                student_id=entry.case.student_id,
                mentor_action=entry.case.mentor_action_type.value,
                priority_score=entry.case.mentor_action_priority,
                escalation_level=entry.case.escalation_level.value,
                case_id=entry.case.case_id,
                case_status=entry.case.status.value,
                opened_at=entry.case.opened_at,
            )
            for entry in entries
        ]
        return MentorQueueResponse(items=items)
