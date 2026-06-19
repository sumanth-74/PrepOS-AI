from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from prepos.application.mentor.mentor_case_ports import MentorCaseRepositoryPort
from prepos.domain.mentor.case_management_v1 import MentorCase, MentorCaseNote
from prepos.domain.mentor.mentor_case_entities import MentorCaseDashboardMetrics, MentorCaseQueueEntry
from prepos.domain.mentor.mentor_types_v1 import (
    CasePriority,
    CaseResolutionReason,
    CaseStatus,
    EscalationLevel,
    MentorActionType,
)
from prepos.infrastructure.db.models.mentor_case import MentorCaseModel, MentorCaseNoteModel


def _map_case(row: MentorCaseModel) -> MentorCase:
    return MentorCase(
        case_id=row.id,
        student_id=row.student_id,
        exam_id=row.exam_id,
        status=CaseStatus(row.status),
        priority=CasePriority(row.priority),
        mentor_action_type=MentorActionType(row.mentor_action_type),
        escalation_level=EscalationLevel(row.escalation_level),
        mentor_action_priority=Decimal(str(row.mentor_action_priority)),
        opened_at=row.opened_at,
        resolved_at=row.resolved_at,
        resolution_reason=(
            CaseResolutionReason(row.resolution_reason)
            if row.resolution_reason is not None
            else None
        ),
    )


def _map_note(row: MentorCaseNoteModel) -> MentorCaseNote:
    return MentorCaseNote(
        id=row.id,
        case_id=row.case_id,
        mentor_id=row.mentor_id,
        note=row.note,
        created_at=row.created_at,
    )


class SqlAlchemyMentorCaseRepository(MentorCaseRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_open_case(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        mentor_action_type: MentorActionType,
    ) -> MentorCase | None:
        result = await self._session.execute(
            select(MentorCaseModel).where(
                MentorCaseModel.tenant_id == tenant_id,
                MentorCaseModel.student_id == student_id,
                MentorCaseModel.exam_id == exam_id,
                MentorCaseModel.mentor_action_type == mentor_action_type.value,
                MentorCaseModel.status == CaseStatus.OPEN.value,
            )
        )
        row = result.scalar_one_or_none()
        return _map_case(row) if row is not None else None

    async def get_case(
        self,
        tenant_id: UUID,
        case_id: UUID,
    ) -> MentorCase | None:
        result = await self._session.execute(
            select(MentorCaseModel).where(
                MentorCaseModel.tenant_id == tenant_id,
                MentorCaseModel.id == case_id,
            )
        )
        row = result.scalar_one_or_none()
        return _map_case(row) if row is not None else None

    async def create_case(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        status: CaseStatus,
        priority: CasePriority,
        mentor_action_type: MentorActionType,
        escalation_level: EscalationLevel,
        mentor_action_priority: Decimal,
        opened_at: datetime,
    ) -> MentorCase:
        now = datetime.now(UTC)
        row = MentorCaseModel(
            id=uuid4(),
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
            status=status.value,
            priority=priority.value,
            mentor_action_type=mentor_action_type.value,
            escalation_level=escalation_level.value,
            mentor_action_priority=mentor_action_priority,
            opened_at=opened_at,
            created_at=now,
            updated_at=now,
        )
        self._session.add(row)
        await self._session.flush()
        return _map_case(row)

    async def update_case_status(
        self,
        *,
        tenant_id: UUID,
        case_id: UUID,
        status: CaseStatus,
    ) -> MentorCase | None:
        result = await self._session.execute(
            select(MentorCaseModel).where(
                MentorCaseModel.tenant_id == tenant_id,
                MentorCaseModel.id == case_id,
            )
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        row.status = status.value
        row.updated_at = datetime.now(UTC)
        await self._session.flush()
        return _map_case(row)

    async def resolve_case(
        self,
        *,
        tenant_id: UUID,
        case_id: UUID,
        resolution_reason: CaseResolutionReason,
        resolved_at: datetime,
    ) -> MentorCase | None:
        result = await self._session.execute(
            select(MentorCaseModel).where(
                MentorCaseModel.tenant_id == tenant_id,
                MentorCaseModel.id == case_id,
            )
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        row.status = CaseStatus.RESOLVED.value
        row.resolution_reason = resolution_reason.value
        row.resolved_at = resolved_at
        row.updated_at = datetime.now(UTC)
        await self._session.flush()
        return _map_case(row)

    async def add_note(
        self,
        *,
        tenant_id: UUID,
        case_id: UUID,
        mentor_id: UUID,
        note: str,
        created_at: datetime,
    ) -> MentorCaseNote:
        case = await self.get_case(tenant_id, case_id)
        if case is None:
            msg = "Mentor case not found."
            raise ValueError(msg)
        row = MentorCaseNoteModel(
            id=uuid4(),
            case_id=case_id,
            mentor_id=mentor_id,
            note=note,
            created_at=created_at,
        )
        self._session.add(row)
        await self._session.flush()
        return _map_note(row)

    async def list_notes(
        self,
        tenant_id: UUID,
        case_id: UUID,
    ) -> tuple[MentorCaseNote, ...]:
        case = await self.get_case(tenant_id, case_id)
        if case is None:
            return ()
        result = await self._session.execute(
            select(MentorCaseNoteModel)
            .where(MentorCaseNoteModel.case_id == case_id)
            .order_by(MentorCaseNoteModel.created_at.asc())
        )
        return tuple(_map_note(row) for row in result.scalars().all())

    async def list_cases(
        self,
        tenant_id: UUID,
        *,
        status: CaseStatus | None = None,
        limit: int = 100,
    ) -> tuple[MentorCase, ...]:
        stmt = select(MentorCaseModel).where(MentorCaseModel.tenant_id == tenant_id)
        if status is not None:
            stmt = stmt.where(MentorCaseModel.status == status.value)
        stmt = stmt.order_by(MentorCaseModel.opened_at.desc()).limit(limit)
        result = await self._session.execute(stmt)
        return tuple(_map_case(row) for row in result.scalars().all())

    async def list_queue(
        self,
        tenant_id: UUID,
        *,
        limit: int = 50,
    ) -> tuple[MentorCaseQueueEntry, ...]:
        active_statuses = (CaseStatus.OPEN.value, CaseStatus.IN_PROGRESS.value)
        result = await self._session.execute(
            select(MentorCaseModel)
            .where(
                MentorCaseModel.tenant_id == tenant_id,
                MentorCaseModel.status.in_(active_statuses),
            )
            .order_by(
                MentorCaseModel.mentor_action_priority.desc(),
                MentorCaseModel.opened_at.asc(),
            )
            .limit(limit)
        )
        return tuple(
            MentorCaseQueueEntry(case=_map_case(row), tenant_id=tenant_id)
            for row in result.scalars().all()
        )

    async def get_dashboard_metrics(
        self,
        tenant_id: UUID,
    ) -> MentorCaseDashboardMetrics:
        open_statuses = (CaseStatus.OPEN.value, CaseStatus.IN_PROGRESS.value)
        open_count = await self._session.scalar(
            select(func.count())
            .select_from(MentorCaseModel)
            .where(
                MentorCaseModel.tenant_id == tenant_id,
                MentorCaseModel.status.in_(open_statuses),
            )
        )
        critical_count = await self._session.scalar(
            select(func.count())
            .select_from(MentorCaseModel)
            .where(
                MentorCaseModel.tenant_id == tenant_id,
                MentorCaseModel.status.in_(open_statuses),
                MentorCaseModel.priority == CasePriority.CRITICAL.value,
            )
        )
        total_cases, resolved_cases, risk_reduced, successful, total_hours = (
            await self.get_effectiveness_inputs(tenant_id)
        )
        from prepos.domain.mentor.mentor_effectiveness_v1 import (
            CaseEffectivenessInputs,
            compute_mentor_effectiveness_v1,
        )

        effectiveness = compute_mentor_effectiveness_v1(
            CaseEffectivenessInputs(
                total_cases=total_cases,
                resolved_cases=resolved_cases,
                risk_reduced_cases=risk_reduced,
                successful_interventions=successful,
                total_resolution_hours=total_hours,
            )
        )
        return MentorCaseDashboardMetrics(
            open_cases=int(open_count or 0),
            critical_cases=int(critical_count or 0),
            average_resolution_time_hours=effectiveness.average_resolution_time_hours,
            mentor_effectiveness_score=effectiveness.effectiveness_score,
        )

    async def get_effectiveness_inputs(
        self,
        tenant_id: UUID,
    ) -> tuple[int, int, int, int, Decimal]:
        total_cases = await self._session.scalar(
            select(func.count())
            .select_from(MentorCaseModel)
            .where(MentorCaseModel.tenant_id == tenant_id)
        )
        resolved_result = await self._session.execute(
            select(MentorCaseModel).where(
                MentorCaseModel.tenant_id == tenant_id,
                MentorCaseModel.status == CaseStatus.RESOLVED.value,
            )
        )
        resolved_rows = resolved_result.scalars().all()
        resolved_cases = len(resolved_rows)
        risk_reduced = sum(
            1
            for row in resolved_rows
            if row.resolution_reason
            in {
                CaseResolutionReason.RISK_REDUCED.value,
                CaseResolutionReason.PLAN_UPDATED.value,
                CaseResolutionReason.GOAL_ADJUSTED.value,
            }
        )
        successful = sum(
            1
            for row in resolved_rows
            if row.resolution_reason != CaseResolutionReason.FALSE_POSITIVE.value
        )
        total_hours = Decimal("0")
        for row in resolved_rows:
            if row.resolved_at is not None:
                delta = row.resolved_at - row.opened_at
                total_hours += Decimal(str(delta.total_seconds())) / Decimal("3600")
        return (
            int(total_cases or 0),
            resolved_cases,
            risk_reduced,
            successful,
            total_hours,
        )

    async def get_active_case_for_student(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
    ) -> MentorCase | None:
        active_statuses = (CaseStatus.OPEN.value, CaseStatus.IN_PROGRESS.value)
        result = await self._session.execute(
            select(MentorCaseModel)
            .where(
                MentorCaseModel.tenant_id == tenant_id,
                MentorCaseModel.student_id == student_id,
                MentorCaseModel.exam_id == exam_id,
                MentorCaseModel.status.in_(active_statuses),
            )
            .order_by(MentorCaseModel.mentor_action_priority.desc())
            .limit(1)
        )
        row = result.scalar_one_or_none()
        return _map_case(row) if row is not None else None
