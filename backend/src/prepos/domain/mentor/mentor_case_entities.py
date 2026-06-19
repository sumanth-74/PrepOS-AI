from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from prepos.domain.mentor.case_management_v1 import MentorCase


@dataclass(frozen=True, slots=True)
class MentorCaseQueueEntry:
    case: MentorCase
    tenant_id: UUID


@dataclass(frozen=True, slots=True)
class MentorCaseDashboardMetrics:
    open_cases: int
    critical_cases: int
    average_resolution_time_hours: Decimal
    mentor_effectiveness_score: Decimal
