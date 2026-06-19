from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from prepos.application.mentor.mentor_case_ports import MentorCaseRepositoryPort
from prepos.application.twin.projection_ports import TwinProjectionRepositoryPort
from prepos.domain.mentor.case_management_v1 import (
    MentorCase,
    map_case_priority,
    should_create_case,
)
from prepos.domain.mentor.events import (
    MentorCaseCreated,
    MentorCaseResolved,
    MentorCaseUpdated,
)
from prepos.domain.mentor.mentor_case_explanations_v1 import (
    explain_case_opened_v1,
    explain_case_resolved_v1,
)
from prepos.domain.mentor.mentor_types_v1 import (
    ActionUrgency,
    CaseResolutionReason,
    CaseStatus,
    EscalationLevel,
    MentorActionType,
)
from prepos.events.outbox.publisher import OutboxPublisher


class MentorCaseService:
    def __init__(
        self,
        *,
        case_repo: MentorCaseRepositoryPort,
        projection_repo: TwinProjectionRepositoryPort,
        outbox: OutboxPublisher,
    ) -> None:
        self._case_repo = case_repo
        self._projection_repo = projection_repo
        self._outbox = outbox

    async def process_mentor_action_updated(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        action_type: MentorActionType,
        priority_score: Decimal,
        urgency: ActionUrgency,
        correlation_id: str,
        causation_id: str | None,
        current_time: datetime | None = None,
    ) -> MentorCase | None:
        if not should_create_case(action_type=action_type):
            return None

        now = current_time or datetime.now(UTC)
        twin = await self._projection_repo.get_projection(tenant_id, student_id, exam_id)
        escalation_level = EscalationLevel.NONE
        if twin is not None and twin.escalation_level is not None:
            escalation_level = EscalationLevel(twin.escalation_level)

        existing = await self._case_repo.get_open_case(
            tenant_id,
            student_id,
            exam_id,
            action_type,
        )
        priority = map_case_priority(urgency=urgency, escalation_level=escalation_level)

        if existing is not None:
            await self._outbox.enqueue_mentor_case_updated(
                MentorCaseUpdated(
                    tenant_id=tenant_id,
                    student_id=student_id,
                    exam_id=exam_id,
                    case_id=existing.case_id,
                    case_status=existing.status,
                    case_priority=existing.priority.value,
                    correlation_id=correlation_id,
                    causation_id=causation_id,
                    occurred_at=now,
                )
            )
            return existing

        created = await self._case_repo.create_case(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
            status=CaseStatus.OPEN,
            priority=priority,
            mentor_action_type=action_type,
            escalation_level=escalation_level,
            mentor_action_priority=priority_score,
            opened_at=now,
        )
        await self._outbox.enqueue_mentor_case_created(
            MentorCaseCreated(
                tenant_id=tenant_id,
                student_id=student_id,
                exam_id=exam_id,
                case_id=created.case_id,
                mentor_action_type=action_type,
                case_status=created.status,
                case_priority=created.priority.value,
                escalation_level=escalation_level,
                priority_score=float(priority_score),
                explanation=explain_case_opened_v1(action_type=action_type),
                correlation_id=correlation_id,
                causation_id=causation_id,
                occurred_at=now,
            )
        )
        return created

    async def add_case_note(
        self,
        *,
        tenant_id: UUID,
        case_id: UUID,
        mentor_id: UUID,
        note: str,
        correlation_id: str,
        causation_id: str | None,
        current_time: datetime | None = None,
    ) -> MentorCase | None:
        now = current_time or datetime.now(UTC)
        case = await self._case_repo.get_case(tenant_id, case_id)
        if case is None:
            return None

        await self._case_repo.add_note(
            tenant_id=tenant_id,
            case_id=case_id,
            mentor_id=mentor_id,
            note=note,
            created_at=now,
        )
        if case.status == CaseStatus.OPEN:
            updated = await self._case_repo.update_case_status(
                tenant_id=tenant_id,
                case_id=case_id,
                status=CaseStatus.IN_PROGRESS,
            )
            if updated is not None:
                await self._outbox.enqueue_mentor_case_updated(
                    MentorCaseUpdated(
                        tenant_id=tenant_id,
                        student_id=updated.student_id,
                        exam_id=updated.exam_id,
                        case_id=updated.case_id,
                        case_status=updated.status,
                        case_priority=updated.priority.value,
                        correlation_id=correlation_id,
                        causation_id=causation_id,
                        occurred_at=now,
                    )
                )
                return updated
        return case

    async def resolve_case(
        self,
        *,
        tenant_id: UUID,
        case_id: UUID,
        resolution_reason: CaseResolutionReason,
        correlation_id: str,
        causation_id: str | None,
        readiness_delta: Decimal | None = None,
        current_time: datetime | None = None,
    ) -> MentorCase | None:
        now = current_time or datetime.now(UTC)
        resolved = await self._case_repo.resolve_case(
            tenant_id=tenant_id,
            case_id=case_id,
            resolution_reason=resolution_reason,
            resolved_at=now,
        )
        if resolved is None:
            return None

        await self._outbox.enqueue_mentor_case_resolved(
            MentorCaseResolved(
                tenant_id=tenant_id,
                student_id=resolved.student_id,
                exam_id=resolved.exam_id,
                case_id=resolved.case_id,
                resolution_reason=resolution_reason,
                explanation=explain_case_resolved_v1(
                    reason=resolution_reason,
                    readiness_delta=readiness_delta,
                ),
                correlation_id=correlation_id,
                causation_id=causation_id,
                occurred_at=now,
            )
        )
        return resolved

    async def get_active_case_payload(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
    ) -> tuple[dict[str, object] | None, str | None, str | None]:
        from prepos.domain.mentor.mentor_payload_v1 import serialize_mentor_case

        active_case = await self._case_repo.get_active_case_for_student(
            tenant_id,
            student_id,
            exam_id,
        )
        if active_case is None:
            return None, None, None
        return (
            serialize_mentor_case(active_case),
            active_case.status.value,
            active_case.priority.value,
        )
