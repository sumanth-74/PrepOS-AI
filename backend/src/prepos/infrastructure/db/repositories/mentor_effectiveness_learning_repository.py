from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from prepos.application.mentor.mentor_effectiveness_learning_ports import (
    MentorEffectivenessLearningRepositoryPort,
)
from prepos.application.twin.intervention_history_ports import InterventionHistoryRepositoryPort
from prepos.domain.mentor.case_management_v1 import MentorCase
from prepos.domain.mentor.mentor_effectiveness_learning_v1 import (
    ActionEffectivenessSample,
    MentorActionEffectiveness,
    MentorEffectivenessLearningResult,
    compute_mentor_effectiveness_learning_v1,
    rank_action_effectiveness_v1,
)
from prepos.domain.mentor.mentor_types_v1 import CaseStatus, MentorActionType
from prepos.infrastructure.db.models.mentor_case import MentorCaseModel
from prepos.infrastructure.db.models.mentor_effectiveness import MentorActionEffectivenessModel


def _map_effectiveness(row: MentorActionEffectivenessModel) -> MentorActionEffectiveness:
    return MentorActionEffectiveness(
        action_type=MentorActionType(row.action_type),
        effectiveness_score=Decimal(str(row.effectiveness_score)),
        readiness_delta=Decimal(str(row.readiness_delta)),
        predicted_score_delta=Decimal(str(row.predicted_score_delta)),
        success_rate=Decimal(str(row.success_rate)),
        sample_size=row.sample_size,
    )


class SqlAlchemyMentorEffectivenessLearningRepository(MentorEffectivenessLearningRepositoryPort):
    def __init__(
        self,
        *,
        session: AsyncSession,
        history_repo: InterventionHistoryRepositoryPort,
    ) -> None:
        self._session = session
        self._history_repo = history_repo

    async def list_learning_samples(
        self,
        tenant_id: UUID,
        *,
        student_id: UUID | None = None,
        exam_id: str | None = None,
    ) -> tuple[ActionEffectivenessSample, ...]:
        stmt = select(MentorCaseModel).where(
            MentorCaseModel.tenant_id == tenant_id,
            MentorCaseModel.status == CaseStatus.RESOLVED.value,
        )
        if student_id is not None:
            stmt = stmt.where(MentorCaseModel.student_id == student_id)
        if exam_id is not None:
            stmt = stmt.where(MentorCaseModel.exam_id == exam_id)
        result = await self._session.execute(stmt)
        rows = result.scalars().all()
        samples: list[ActionEffectivenessSample] = []
        for row in rows:
            outcomes = await self._history_repo.list_outcomes(
                tenant_id,
                row.student_id,
                row.exam_id,
            )
            relevant = [
                outcome
                for outcome in outcomes
                if outcome.created_at >= row.opened_at
                and (
                    row.resolved_at is None
                    or outcome.created_at <= row.resolved_at
                )
            ]
            if relevant:
                readiness_delta = sum(item.readiness_delta for item in relevant) / Decimal(
                    len(relevant)
                )
                predicted_score_delta = sum(
                    item.predicted_score_delta for item in relevant
                ) / Decimal(len(relevant))
            else:
                readiness_delta = Decimal("0")
                predicted_score_delta = Decimal("0")
            from prepos.domain.mentor.mentor_types_v1 import CaseResolutionReason

            resolution_reason = (
                CaseResolutionReason(row.resolution_reason)
                if row.resolution_reason is not None
                else None
            )
            samples.append(
                ActionEffectivenessSample(
                    action_type=MentorActionType(row.mentor_action_type),
                    resolution_reason=resolution_reason,
                    readiness_delta=readiness_delta,
                    predicted_score_delta=predicted_score_delta,
                )
            )
        return tuple(samples)

    async def upsert_action_effectiveness(
        self,
        tenant_id: UUID,
        action_effectiveness: tuple[MentorActionEffectiveness, ...],
    ) -> None:
        now = datetime.now(UTC)
        for item in action_effectiveness:
            stmt = insert(MentorActionEffectivenessModel).values(
                tenant_id=tenant_id,
                action_type=item.action_type.value,
                effectiveness_score=item.effectiveness_score,
                readiness_delta=item.readiness_delta,
                predicted_score_delta=item.predicted_score_delta,
                success_rate=item.success_rate,
                sample_size=item.sample_size,
                updated_at=now,
            )
            upsert_stmt = stmt.on_conflict_do_update(
                index_elements=["tenant_id", "action_type"],
                set_={
                    "effectiveness_score": item.effectiveness_score,
                    "readiness_delta": item.readiness_delta,
                    "predicted_score_delta": item.predicted_score_delta,
                    "success_rate": item.success_rate,
                    "sample_size": item.sample_size,
                    "updated_at": now,
                },
            )
            await self._session.execute(upsert_stmt)
        await self._session.flush()

    async def list_action_effectiveness(
        self,
        tenant_id: UUID,
    ) -> tuple[MentorActionEffectiveness, ...]:
        result = await self._session.execute(
            select(MentorActionEffectivenessModel).where(
                MentorActionEffectivenessModel.tenant_id == tenant_id
            )
        )
        rows = result.scalars().all()
        return rank_action_effectiveness_v1(tuple(_map_effectiveness(row) for row in rows))

    async def get_action_effectiveness(
        self,
        tenant_id: UUID,
        action_type: str,
    ) -> MentorActionEffectiveness | None:
        result = await self._session.execute(
            select(MentorActionEffectivenessModel).where(
                MentorActionEffectivenessModel.tenant_id == tenant_id,
                MentorActionEffectivenessModel.action_type == action_type,
            )
        )
        row = result.scalar_one_or_none()
        return _map_effectiveness(row) if row is not None else None

    async def get_tenant_learning_summary(
        self,
        tenant_id: UUID,
    ) -> MentorEffectivenessLearningResult:
        stored = await self.list_action_effectiveness(tenant_id)
        if stored:
            best = stored[0]
            total_weight = sum(item.sample_size for item in stored)
            weighted_average = (
                sum(item.effectiveness_score * Decimal(item.sample_size) for item in stored)
                / Decimal(total_weight)
                if total_weight > 0
                else Decimal("0")
            )
            from prepos.domain.scoring.common import round_score

            return MentorEffectivenessLearningResult(
                action_effectiveness=stored,
                best_action=best.action_type,
                best_action_effectiveness=best.effectiveness_score,
                average_action_effectiveness=round_score(weighted_average),
            )
        samples = await self.list_learning_samples(tenant_id)
        return compute_mentor_effectiveness_learning_v1(samples)

    async def get_student_learning_summary(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
    ) -> MentorEffectivenessLearningResult:
        samples = await self.list_learning_samples(
            tenant_id,
            student_id=student_id,
            exam_id=exam_id,
        )
        return compute_mentor_effectiveness_learning_v1(samples)
