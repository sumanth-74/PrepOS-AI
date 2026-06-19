from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from prepos.domain.mentor.case_management_v1 import MentorCase, MentorCaseNote
from prepos.domain.mentor.mentor_case_entities import MentorCaseDashboardMetrics, MentorCaseQueueEntry
from prepos.domain.mentor.mentor_types_v1 import (
    CasePriority,
    CaseResolutionReason,
    CaseStatus,
    EscalationLevel,
    MentorActionType,
)


class MentorCaseRepositoryPort(ABC):
    @abstractmethod
    async def get_open_case(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        mentor_action_type: MentorActionType,
    ) -> MentorCase | None:
        raise NotImplementedError

    @abstractmethod
    async def get_case(
        self,
        tenant_id: UUID,
        case_id: UUID,
    ) -> MentorCase | None:
        raise NotImplementedError

    @abstractmethod
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
        raise NotImplementedError

    @abstractmethod
    async def update_case_status(
        self,
        *,
        tenant_id: UUID,
        case_id: UUID,
        status: CaseStatus,
    ) -> MentorCase | None:
        raise NotImplementedError

    @abstractmethod
    async def resolve_case(
        self,
        *,
        tenant_id: UUID,
        case_id: UUID,
        resolution_reason: CaseResolutionReason,
        resolved_at: datetime,
    ) -> MentorCase | None:
        raise NotImplementedError

    @abstractmethod
    async def add_note(
        self,
        *,
        tenant_id: UUID,
        case_id: UUID,
        mentor_id: UUID,
        note: str,
        created_at: datetime,
    ) -> MentorCaseNote:
        raise NotImplementedError

    @abstractmethod
    async def list_notes(
        self,
        tenant_id: UUID,
        case_id: UUID,
    ) -> tuple[MentorCaseNote, ...]:
        raise NotImplementedError

    @abstractmethod
    async def list_cases(
        self,
        tenant_id: UUID,
        *,
        status: CaseStatus | None = None,
        limit: int = 100,
    ) -> tuple[MentorCase, ...]:
        raise NotImplementedError

    @abstractmethod
    async def list_queue(
        self,
        tenant_id: UUID,
        *,
        limit: int = 50,
    ) -> tuple[MentorCaseQueueEntry, ...]:
        raise NotImplementedError

    @abstractmethod
    async def get_dashboard_metrics(
        self,
        tenant_id: UUID,
    ) -> MentorCaseDashboardMetrics:
        raise NotImplementedError

    @abstractmethod
    async def get_effectiveness_inputs(
        self,
        tenant_id: UUID,
    ) -> tuple[int, int, int, int, Decimal]:
        raise NotImplementedError

    @abstractmethod
    async def get_active_case_for_student(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
    ) -> MentorCase | None:
        raise NotImplementedError
