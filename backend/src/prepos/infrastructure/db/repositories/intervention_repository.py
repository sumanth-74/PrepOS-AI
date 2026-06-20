from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from prepos.application.interventions.ports import InterventionRepositoryPort
from prepos.infrastructure.db.models.mentor_interventions import (
    InterventionEffectivenessModel,
    InterventionRecommendationModel,
    MentorInterventionModel,
)
from prepos.infrastructure.db.models.student import StudentModel


class SqlAlchemyInterventionRepository(InterventionRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_recommendations(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        recommendations: list[dict[str, object]],
        now: datetime,
    ) -> list[UUID]:
        ids: list[UUID] = []
        for recommendation in recommendations:
            recommendation_id = uuid4()
            ids.append(recommendation_id)
            self._session.add(
                InterventionRecommendationModel(
                    id=recommendation_id,
                    tenant_id=tenant_id,
                    student_id=student_id,
                    exam_id=exam_id,
                    intervention_type=str(recommendation["intervention_type"]),
                    concept_id=str(recommendation["concept_id"]) if recommendation.get("concept_id") else None,
                    recommendation_reason=str(recommendation["recommendation_reason"]),
                    impact_score=recommendation["impact_score"],  # type: ignore[arg-type]
                    confidence=str(recommendation["confidence"]),
                    predicted_gain=recommendation["predicted_gain"],  # type: ignore[arg-type]
                    created_at=now,
                )
            )
        await self._session.flush()
        return ids

    async def create_intervention(
        self,
        *,
        tenant_id: UUID,
        mentor_id: UUID,
        student_id: UUID,
        exam_id: str,
        intervention_type: str,
        concept_id: str | None,
        reason: str,
        predicted_gain: float,
        priority_score: float,
        status: str,
        metadata_json: dict[str, object],
        now: datetime,
    ) -> UUID:
        intervention_id = uuid4()
        self._session.add(
            MentorInterventionModel(
                id=intervention_id,
                tenant_id=tenant_id,
                mentor_id=mentor_id,
                student_id=student_id,
                exam_id=exam_id,
                intervention_type=intervention_type,
                concept_id=concept_id,
                reason=reason,
                predicted_gain=predicted_gain,
                priority_score=priority_score,
                status=status,
                metadata_json=metadata_json,
                created_at=now,
            )
        )
        await self._session.flush()
        return intervention_id

    async def get_intervention(
        self,
        *,
        tenant_id: UUID,
        intervention_id: UUID,
    ) -> dict[str, object] | None:
        stmt = select(MentorInterventionModel).where(
            MentorInterventionModel.tenant_id == tenant_id,
            MentorInterventionModel.id == intervention_id,
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return self._intervention_to_dict(row) if row else None

    async def list_student_interventions(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str | None,
        limit: int,
    ) -> list[dict[str, object]]:
        stmt = select(MentorInterventionModel).where(
            MentorInterventionModel.tenant_id == tenant_id,
            MentorInterventionModel.student_id == student_id,
        )
        if exam_id:
            stmt = stmt.where(MentorInterventionModel.exam_id == exam_id)
        stmt = stmt.order_by(MentorInterventionModel.created_at.desc()).limit(limit)
        rows = (await self._session.execute(stmt)).scalars().all()
        return [self._intervention_to_dict(row) for row in rows]

    async def list_student_recommendations(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        limit: int,
    ) -> list[dict[str, object]]:
        stmt = (
            select(InterventionRecommendationModel)
            .where(
                InterventionRecommendationModel.tenant_id == tenant_id,
                InterventionRecommendationModel.student_id == student_id,
                InterventionRecommendationModel.exam_id == exam_id,
            )
            .order_by(InterventionRecommendationModel.impact_score.desc(), InterventionRecommendationModel.created_at.desc())
            .limit(limit)
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [
            {
                "id": row.id,
                "intervention_type": row.intervention_type,
                "concept_id": row.concept_id,
                "recommendation_reason": row.recommendation_reason,
                "impact_score": float(row.impact_score),
                "confidence": row.confidence,
                "predicted_gain": float(row.predicted_gain),
                "created_at": row.created_at,
            }
            for row in rows
        ]

    async def list_student_history(
        self,
        *,
        tenant_id: UUID,
        student_user_id: UUID,
        exam_id: str | None,
        limit: int,
    ) -> list[dict[str, object]]:
        student_stmt = select(StudentModel.id).where(
            StudentModel.tenant_id == tenant_id,
            StudentModel.user_id == student_user_id,
        )
        student_id = (await self._session.execute(student_stmt)).scalar_one_or_none()
        if student_id is None:
            return []
        stmt = (
            select(MentorInterventionModel, InterventionEffectivenessModel)
            .outerjoin(
                InterventionEffectivenessModel,
                InterventionEffectivenessModel.intervention_id == MentorInterventionModel.id,
            )
            .where(
                MentorInterventionModel.tenant_id == tenant_id,
                MentorInterventionModel.student_id == student_id,
            )
        )
        if exam_id:
            stmt = stmt.where(MentorInterventionModel.exam_id == exam_id)
        stmt = stmt.order_by(MentorInterventionModel.created_at.desc()).limit(limit)
        rows = (await self._session.execute(stmt)).all()
        result: list[dict[str, object]] = []
        for intervention, effectiveness in rows:
            item = self._intervention_to_dict(intervention)
            item["intervention_id"] = intervention.id
            if effectiveness is not None:
                item["actual_gain"] = float(effectiveness.actual_gain)
                item["effectiveness_score"] = float(effectiveness.effectiveness_score)
                item["evaluated_at"] = effectiveness.evaluated_at
            result.append(item)
        return result

    async def list_mentor_queue(
        self,
        *,
        tenant_id: UUID,
        mentor_id: UUID,
        limit: int,
    ) -> list[dict[str, object]]:
        stmt = (
            select(MentorInterventionModel)
            .where(
                MentorInterventionModel.tenant_id == tenant_id,
                MentorInterventionModel.status.in_(("pending", "in_progress")),
            )
            .order_by(MentorInterventionModel.priority_score.desc(), MentorInterventionModel.created_at.desc())
            .limit(limit)
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        if rows:
            return [self._intervention_to_dict(row) for row in rows]

        rec_stmt = (
            select(InterventionRecommendationModel)
            .where(InterventionRecommendationModel.tenant_id == tenant_id)
            .order_by(
                InterventionRecommendationModel.impact_score.desc(),
                InterventionRecommendationModel.created_at.desc(),
            )
            .limit(limit)
        )
        rec_rows = (await self._session.execute(rec_stmt)).scalars().all()
        return [
            {
                "student_id": row.student_id,
                "exam_id": row.exam_id,
                "intervention_type": row.intervention_type,
                "concept_id": row.concept_id,
                "priority_score": float(row.impact_score),
                "predicted_gain": float(row.predicted_gain),
                "reason": row.recommendation_reason,
                "forecast_status": None,
            }
            for row in rec_rows
        ]

    async def update_intervention_status(
        self,
        *,
        tenant_id: UUID,
        intervention_id: UUID,
        status: str,
    ) -> None:
        stmt = select(MentorInterventionModel).where(
            MentorInterventionModel.tenant_id == tenant_id,
            MentorInterventionModel.id == intervention_id,
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        if row is None:
            return
        row.status = status
        await self._session.flush()

    async def record_effectiveness(
        self,
        *,
        intervention_id: UUID,
        readiness_before: float,
        readiness_after: float,
        actual_gain: float,
        effectiveness_score: float,
        now: datetime,
    ) -> UUID:
        effectiveness_id = uuid4()
        self._session.add(
            InterventionEffectivenessModel(
                id=effectiveness_id,
                intervention_id=intervention_id,
                readiness_before=readiness_before,
                readiness_after=readiness_after,
                actual_gain=actual_gain,
                effectiveness_score=effectiveness_score,
                evaluated_at=now,
            )
        )
        await self._session.flush()
        return effectiveness_id

    async def get_effectiveness_history(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        limit: int,
    ) -> list[dict[str, object]]:
        stmt = (
            select(MentorInterventionModel, InterventionEffectivenessModel)
            .join(
                InterventionEffectivenessModel,
                InterventionEffectivenessModel.intervention_id == MentorInterventionModel.id,
            )
            .where(
                MentorInterventionModel.tenant_id == tenant_id,
                MentorInterventionModel.student_id == student_id,
            )
            .order_by(InterventionEffectivenessModel.evaluated_at.desc())
            .limit(limit)
        )
        rows = (await self._session.execute(stmt)).all()
        return [
            {
                "intervention_id": intervention.id,
                "intervention_type": intervention.intervention_type,
                "concept_id": intervention.concept_id,
                "predicted_gain": float(intervention.predicted_gain),
                "actual_gain": float(effectiveness.actual_gain),
                "effectiveness_score": float(effectiveness.effectiveness_score),
                "created_at": intervention.created_at,
                "evaluated_at": effectiveness.evaluated_at,
            }
            for intervention, effectiveness in rows
        ]

    async def get_admin_metrics(self, *, tenant_id: UUID) -> dict[str, object]:
        since = datetime.now(UTC) - timedelta(days=30)
        total_stmt = select(func.count()).select_from(MentorInterventionModel).where(
            MentorInterventionModel.tenant_id == tenant_id
        )
        total = int((await self._session.execute(total_stmt)).scalar_one())
        recent_stmt = select(func.count()).select_from(MentorInterventionModel).where(
            MentorInterventionModel.tenant_id == tenant_id,
            MentorInterventionModel.created_at >= since,
        )
        recent = int((await self._session.execute(recent_stmt)).scalar_one())

        effectiveness_stmt = (
            select(
                func.avg(InterventionEffectivenessModel.actual_gain),
                func.avg(InterventionEffectivenessModel.effectiveness_score),
            )
            .join(MentorInterventionModel, MentorInterventionModel.id == InterventionEffectivenessModel.intervention_id)
            .where(MentorInterventionModel.tenant_id == tenant_id)
        )
        avg_gain, avg_effectiveness = (await self._session.execute(effectiveness_stmt)).one()
        success_stmt = select(func.count()).select_from(InterventionEffectivenessModel).join(
            MentorInterventionModel,
            MentorInterventionModel.id == InterventionEffectivenessModel.intervention_id,
        ).where(
            MentorInterventionModel.tenant_id == tenant_id,
            InterventionEffectivenessModel.effectiveness_score >= 80,
        )
        success_count = int((await self._session.execute(success_stmt)).scalar_one())
        completed_stmt = select(func.count()).select_from(InterventionEffectivenessModel).join(
            MentorInterventionModel,
            MentorInterventionModel.id == InterventionEffectivenessModel.intervention_id,
        ).where(MentorInterventionModel.tenant_id == tenant_id)
        completed_count = int((await self._session.execute(completed_stmt)).scalar_one())
        success_rate = (success_count / completed_count) if completed_count else 0.0

        top_stmt = (
            select(MentorInterventionModel.intervention_type, func.count())
            .where(MentorInterventionModel.tenant_id == tenant_id)
            .group_by(MentorInterventionModel.intervention_type)
            .order_by(func.count().desc())
            .limit(5)
        )
        top_rows = (await self._session.execute(top_stmt)).all()
        top_interventions = [{"intervention_type": row[0], "count": row[1]} for row in top_rows]

        least_stmt = (
            select(
                MentorInterventionModel.intervention_type,
                func.avg(InterventionEffectivenessModel.effectiveness_score),
            )
            .join(
                InterventionEffectivenessModel,
                InterventionEffectivenessModel.intervention_id == MentorInterventionModel.id,
            )
            .where(MentorInterventionModel.tenant_id == tenant_id)
            .group_by(MentorInterventionModel.intervention_type)
            .order_by(func.avg(InterventionEffectivenessModel.effectiveness_score).asc())
            .limit(5)
        )
        least_rows = (await self._session.execute(least_stmt)).all()
        least_effective = [
            {"intervention_type": row[0], "average_effectiveness": float(row[1] or 0)} for row in least_rows
        ]

        status_stmt = (
            select(MentorInterventionModel.status, func.count())
            .where(MentorInterventionModel.tenant_id == tenant_id)
            .group_by(MentorInterventionModel.status)
        )
        status_rows = (await self._session.execute(status_stmt)).all()
        status_counts = [{"status": row[0], "count": row[1]} for row in status_rows]

        return {
            "total_interventions": total,
            "interventions_last_30_days": recent,
            "average_gain": round(float(avg_gain or 0), 2),
            "average_effectiveness": round(float(avg_effectiveness or 0), 2),
            "mentor_success_rate": round(success_rate, 4),
            "top_interventions": top_interventions,
            "least_effective_interventions": least_effective,
            "status_counts": status_counts,
        }

    async def export_rows(self, *, tenant_id: UUID, limit: int) -> list[dict[str, object]]:
        stmt = (
            select(MentorInterventionModel, InterventionEffectivenessModel)
            .outerjoin(
                InterventionEffectivenessModel,
                InterventionEffectivenessModel.intervention_id == MentorInterventionModel.id,
            )
            .where(MentorInterventionModel.tenant_id == tenant_id)
            .order_by(MentorInterventionModel.created_at.desc())
            .limit(limit)
        )
        rows = (await self._session.execute(stmt)).all()
        return [
            {
                "intervention_id": intervention.id,
                "student_id": intervention.student_id,
                "intervention_type": intervention.intervention_type,
                "concept_id": intervention.concept_id,
                "predicted_gain": float(intervention.predicted_gain),
                "actual_gain": float(effectiveness.actual_gain) if effectiveness else None,
                "effectiveness_score": float(effectiveness.effectiveness_score) if effectiveness else None,
                "status": intervention.status,
                "created_at": intervention.created_at.isoformat(),
            }
            for intervention, effectiveness in rows
        ]

    @staticmethod
    def _intervention_to_dict(row: MentorInterventionModel) -> dict[str, object]:
        return {
            "id": row.id,
            "tenant_id": row.tenant_id,
            "mentor_id": row.mentor_id,
            "student_id": row.student_id,
            "exam_id": row.exam_id,
            "intervention_type": row.intervention_type,
            "concept_id": row.concept_id,
            "reason": row.reason,
            "predicted_gain": float(row.predicted_gain),
            "priority_score": float(row.priority_score),
            "status": row.status,
            "metadata_json": row.metadata_json,
            "created_at": row.created_at,
        }
