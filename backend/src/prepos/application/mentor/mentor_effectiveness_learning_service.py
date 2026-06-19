from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from prepos.application.mentor.mentor_effectiveness_learning_ports import (
    MentorEffectivenessLearningRepositoryPort,
)
from prepos.domain.mentor.events import MentorEffectivenessUpdated
from prepos.domain.mentor.mentor_effectiveness_v1 import (
    CaseEffectivenessInputs,
    compute_mentor_effectiveness_v1,
)
from prepos.domain.mentor.mentor_effectiveness_learning_v1 import (
    MentorEffectivenessLearningResult,
    compute_mentor_effectiveness_learning_v1,
)
from prepos.events.outbox.publisher import OutboxPublisher


@dataclass(frozen=True, slots=True)
class MentorEffectivenessSnapshot:
    tenant_summary: MentorEffectivenessLearningResult
    student_summary: MentorEffectivenessLearningResult
    mentor_payload_patch: dict[str, object]


class MentorEffectivenessLearningService:
    def __init__(
        self,
        *,
        learning_repo: MentorEffectivenessLearningRepositoryPort,
        case_repo: object,
        outbox: OutboxPublisher,
    ) -> None:
        self._learning_repo = learning_repo
        self._case_repo = case_repo
        self._outbox = outbox

    async def recompute_and_publish(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        correlation_id: str,
        causation_id: str | None,
        current_time: datetime | None = None,
    ) -> MentorEffectivenessSnapshot:
        now = current_time or datetime.now(UTC)
        tenant_samples = await self._learning_repo.list_learning_samples(tenant_id)
        tenant_computed = compute_mentor_effectiveness_learning_v1(tenant_samples)
        await self._learning_repo.upsert_action_effectiveness(
            tenant_id,
            tenant_computed.action_effectiveness,
        )
        tenant_summary = await self._learning_repo.get_tenant_learning_summary(tenant_id)
        student_summary = await self._learning_repo.get_student_learning_summary(
            tenant_id,
            student_id,
            exam_id,
        )
        mentor_payload_patch = self._build_payload_patch(student_summary)
        await self._publish_effectiveness_updated(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
            tenant_summary=tenant_summary,
            correlation_id=correlation_id,
            causation_id=causation_id,
            current_time=now,
        )
        return MentorEffectivenessSnapshot(
            tenant_summary=tenant_summary,
            student_summary=student_summary,
            mentor_payload_patch=mentor_payload_patch,
        )

    async def get_student_effectiveness_payload(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
    ) -> dict[str, object]:
        student_summary = await self._learning_repo.get_student_learning_summary(
            tenant_id,
            student_id,
            exam_id,
        )
        return self._build_payload_patch(student_summary)

    async def get_action_effectiveness_score(
        self,
        *,
        tenant_id: UUID,
        action_type: str,
    ) -> Decimal:
        effectiveness = await self._learning_repo.get_action_effectiveness(
            tenant_id,
            action_type,
        )
        if effectiveness is None:
            return Decimal("0")
        return effectiveness.effectiveness_score

    def _build_payload_patch(
        self,
        student_summary: MentorEffectivenessLearningResult,
    ) -> dict[str, object]:
        from prepos.domain.mentor.mentor_payload_v1 import serialize_mentor_effectiveness

        if student_summary.best_action is None:
            return {}
        best = next(
            (
                item
                for item in student_summary.action_effectiveness
                if item.action_type == student_summary.best_action
            ),
            None,
        )
        if best is None:
            return {}
        return {
            "mentor_effectiveness": serialize_mentor_effectiveness(
                best_action=best.action_type,
                effectiveness_score=best.effectiveness_score,
                sample_size=best.sample_size,
            )
        }

    async def _publish_effectiveness_updated(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        tenant_summary: MentorEffectivenessLearningResult,
        correlation_id: str,
        causation_id: str | None,
        current_time: datetime,
    ) -> None:
        total_cases, resolved_cases, risk_reduced, successful, total_hours = (
            await self._case_repo.get_effectiveness_inputs(tenant_id)
        )
        legacy = compute_mentor_effectiveness_v1(
            CaseEffectivenessInputs(
                total_cases=total_cases,
                resolved_cases=resolved_cases,
                risk_reduced_cases=risk_reduced,
                successful_interventions=successful,
                total_resolution_hours=total_hours,
            )
        )
        await self._outbox.enqueue_mentor_effectiveness_updated(
            MentorEffectivenessUpdated(
                tenant_id=tenant_id,
                student_id=student_id,
                exam_id=exam_id,
                effectiveness_score=float(legacy.effectiveness_score),
                cases_resolved=legacy.cases_resolved,
                average_resolution_time_hours=float(legacy.average_resolution_time_hours),
                risk_reduction_rate=float(legacy.risk_reduction_rate),
                best_action=(
                    tenant_summary.best_action.value
                    if tenant_summary.best_action is not None
                    else None
                ),
                best_action_effectiveness=float(tenant_summary.best_action_effectiveness),
                average_action_effectiveness=float(tenant_summary.average_action_effectiveness),
                correlation_id=correlation_id,
                causation_id=causation_id,
                occurred_at=current_time,
            )
        )
