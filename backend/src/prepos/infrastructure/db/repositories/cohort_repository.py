from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from prepos.application.cohort.ports import CohortRepositoryPort
from prepos.infrastructure.db.models.cohort_intelligence import (
    CohortEventModel,
    CohortSnapshotModel,
    CohortTrendModel,
    StudentSegmentModel,
)
from prepos.infrastructure.db.models.goal_forecasting import GoalForecastModel
from prepos.infrastructure.db.models.mentor_interventions import (
    InterventionEffectivenessModel,
    MentorInterventionModel,
)
from prepos.infrastructure.db.models.student import PreparationTwinModel, StudentModel


class SqlAlchemyCohortRepository(CohortRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_cohort_student_rows(
        self,
        *,
        tenant_id: UUID,
        exam_id: str,
    ) -> list[dict[str, object]]:
        stmt = (
            select(StudentModel, PreparationTwinModel)
            .outerjoin(
                PreparationTwinModel,
                (PreparationTwinModel.student_id == StudentModel.id)
                & (PreparationTwinModel.tenant_id == StudentModel.tenant_id)
                & (PreparationTwinModel.exam_id == exam_id),
            )
            .where(
                StudentModel.tenant_id == tenant_id,
                StudentModel.onboarding_completed.is_(True),
            )
        )
        rows = (await self._session.execute(stmt)).all()
        student_ids = [student.id for student, _ in rows if student.target_exam_id in {None, exam_id}]
        if not student_ids:
            student_ids = [student.id for student, _ in rows]

        forecast_map = await self._forecast_map(tenant_id=tenant_id, exam_id=exam_id, student_ids=student_ids)
        intervention_map = await self._intervention_map(tenant_id=tenant_id, student_ids=student_ids)

        result: list[dict[str, object]] = []
        for student, twin in rows:
            if student.target_exam_id not in {None, exam_id}:
                continue
            payload = dict(twin.twin_payload) if twin is not None else {}
            forecast = payload.get("forecast") if isinstance(payload.get("forecast"), dict) else {}
            study_behavior = payload.get("study_behavior") if isinstance(payload.get("study_behavior"), dict) else {}
            drivers = payload.get("drivers") if isinstance(payload.get("drivers"), dict) else {}
            negative = drivers.get("top_negative_drivers")
            negative_drivers = [str(item) for item in negative] if isinstance(negative, list) else []

            readiness = float(twin.readiness_score or 0.0) if twin else 0.0
            student_forecast = forecast_map.get(student.id, {})
            forecast_probability = float(
                student_forecast.get("probability_of_success", forecast.get("goal_probability", 50.0)) or 50.0
            )
            projected = float(
                student_forecast.get("projected_readiness", forecast.get("projected_readiness", readiness)) or readiness
            )
            on_track = bool(forecast.get("on_track", projected >= 60))
            completion = float(study_behavior.get("completion_rate", 0.5) or 0.5) * 100.0
            weekly_progress = float(forecast.get("expected_weekly_progress", 1.0) or 1.0)
            consistency = float(twin.consistency_score or 50.0) if twin else 50.0
            historical = float(twin.historical_effectiveness or 50.0) if twin else 50.0

            intervention_stats = intervention_map.get(student.id, {})
            result.append(
                {
                    "student_id": student.id,
                    "user_id": student.user_id,
                    "exam_id": exam_id,
                    "target_year": student.target_year,
                    "readiness": readiness,
                    "forecast_probability": forecast_probability,
                    "projected_readiness": projected,
                    "on_track": on_track,
                    "goal_attainment": forecast_probability,
                    "planning_adherence": completion,
                    "recommendation_effectiveness": historical,
                    "intervention_effectiveness": float(intervention_stats.get("avg_effectiveness", 50.0)),
                    "intervention_count": int(intervention_stats.get("count", 0)),
                    "failed_intervention_count": int(intervention_stats.get("failed_count", 0)),
                    "readiness_delta": float(intervention_stats.get("avg_gain", weekly_progress)),
                    "weekly_progress": weekly_progress,
                    "consistency_score": consistency,
                    "pyq_preparedness": min(100.0, historical + 5.0),
                    "current_affairs_preparedness": min(100.0, completion),
                    "negative_drivers": negative_drivers,
                }
            )
        return result

    async def _forecast_map(
        self,
        *,
        tenant_id: UUID,
        exam_id: str,
        student_ids: list[UUID],
    ) -> dict[UUID, dict[str, object]]:
        if not student_ids:
            return {}
        stmt = (
            select(GoalForecastModel)
            .where(
                GoalForecastModel.tenant_id == tenant_id,
                GoalForecastModel.exam_id == exam_id,
                GoalForecastModel.student_id.in_(student_ids),
            )
            .order_by(GoalForecastModel.created_at.desc())
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        mapping: dict[UUID, dict[str, object]] = {}
        for row in rows:
            if row.student_id in mapping:
                continue
            mapping[row.student_id] = {
                "probability_of_success": float(row.probability_of_success),
                "projected_readiness": float(row.projected_readiness),
            }
        return mapping

    async def _intervention_map(
        self,
        *,
        tenant_id: UUID,
        student_ids: list[UUID],
    ) -> dict[UUID, dict[str, object]]:
        if not student_ids:
            return {}
        stmt = (
            select(
                MentorInterventionModel.student_id,
                func.count(MentorInterventionModel.id),
                func.avg(InterventionEffectivenessModel.effectiveness_score),
                func.avg(InterventionEffectivenessModel.actual_gain),
            )
            .outerjoin(
                InterventionEffectivenessModel,
                InterventionEffectivenessModel.intervention_id == MentorInterventionModel.id,
            )
            .where(
                MentorInterventionModel.tenant_id == tenant_id,
                MentorInterventionModel.student_id.in_(student_ids),
            )
            .group_by(MentorInterventionModel.student_id)
        )
        rows = (await self._session.execute(stmt)).all()
        mapping: dict[UUID, dict[str, object]] = {}
        for student_id, count, avg_eff, avg_gain in rows:
            failed_stmt = select(func.count()).select_from(InterventionEffectivenessModel).join(
                MentorInterventionModel,
                MentorInterventionModel.id == InterventionEffectivenessModel.intervention_id,
            ).where(
                MentorInterventionModel.tenant_id == tenant_id,
                MentorInterventionModel.student_id == student_id,
                InterventionEffectivenessModel.effectiveness_score < 40,
            )
            failed_count = int((await self._session.execute(failed_stmt)).scalar_one())
            mapping[student_id] = {
                "count": int(count or 0),
                "avg_effectiveness": float(avg_eff or 50.0),
                "avg_gain": float(avg_gain or 0.0),
                "failed_count": failed_count,
            }
        return mapping

    async def save_snapshot(
        self,
        *,
        tenant_id: UUID,
        cohort_id: str,
        exam_id: str,
        snapshot_date: date,
        student_count: int,
        avg_readiness: float,
        avg_forecast: float,
        avg_effectiveness: float,
        risk_count: int,
        segment_counts: dict[str, int],
        metadata_json: dict[str, object],
        now: datetime,
    ) -> UUID:
        snapshot_id = uuid4()
        self._session.add(
            CohortSnapshotModel(
                id=snapshot_id,
                tenant_id=tenant_id,
                cohort_id=cohort_id,
                exam_id=exam_id,
                snapshot_date=snapshot_date,
                student_count=student_count,
                avg_readiness=avg_readiness,
                avg_forecast=avg_forecast,
                avg_effectiveness=avg_effectiveness,
                risk_count=risk_count,
                segment_counts_json=segment_counts,
                metadata_json=metadata_json,
                created_at=now,
            )
        )
        await self._session.flush()
        return snapshot_id

    async def save_segments(
        self,
        *,
        tenant_id: UUID,
        cohort_id: str,
        segments: list[dict[str, object]],
        now: datetime,
    ) -> None:
        for segment in segments:
            self._session.add(
                StudentSegmentModel(
                    id=uuid4(),
                    tenant_id=tenant_id,
                    cohort_id=cohort_id,
                    student_id=segment["student_id"],  # type: ignore[index]
                    segment_type=str(segment["segment_type"]),
                    segment_score=segment["segment_score"],  # type: ignore[arg-type]
                    risk_score=segment["risk_score"],  # type: ignore[arg-type]
                    metadata_json=dict(segment.get("metadata_json") or {}),
                    calculated_at=now,
                )
            )
        await self._session.flush()

    async def save_trends(
        self,
        *,
        tenant_id: UUID,
        cohort_id: str,
        trends: list[dict[str, object]],
        now: datetime,
    ) -> None:
        for trend in trends:
            self._session.add(
                CohortTrendModel(
                    id=uuid4(),
                    tenant_id=tenant_id,
                    cohort_id=cohort_id,
                    concept_id=str(trend["concept_id"]),
                    trend_direction=str(trend["trend_direction"]),
                    readiness_delta=trend["readiness_delta"],  # type: ignore[arg-type]
                    period=str(trend.get("period", "weekly")),
                    created_at=now,
                )
            )
        await self._session.flush()

    async def record_event(
        self,
        *,
        tenant_id: UUID,
        cohort_id: str | None,
        event_type: str,
        metadata_json: dict[str, object],
        now: datetime,
    ) -> UUID:
        event_id = uuid4()
        self._session.add(
            CohortEventModel(
                id=event_id,
                tenant_id=tenant_id,
                cohort_id=cohort_id,
                event_type=event_type,
                metadata_json=metadata_json,
                created_at=now,
            )
        )
        await self._session.flush()
        return event_id

    async def get_latest_snapshot(
        self,
        *,
        tenant_id: UUID,
        cohort_id: str,
    ) -> dict[str, object] | None:
        stmt = (
            select(CohortSnapshotModel)
            .where(
                CohortSnapshotModel.tenant_id == tenant_id,
                CohortSnapshotModel.cohort_id == cohort_id,
            )
            .order_by(CohortSnapshotModel.created_at.desc())
            .limit(1)
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return self._snapshot_to_dict(row) if row else None

    async def get_previous_snapshot(
        self,
        *,
        tenant_id: UUID,
        cohort_id: str,
        before_date: date,
    ) -> dict[str, object] | None:
        stmt = (
            select(CohortSnapshotModel)
            .where(
                CohortSnapshotModel.tenant_id == tenant_id,
                CohortSnapshotModel.cohort_id == cohort_id,
                CohortSnapshotModel.snapshot_date < before_date,
            )
            .order_by(CohortSnapshotModel.snapshot_date.desc())
            .limit(1)
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return self._snapshot_to_dict(row) if row else None

    async def list_segments(
        self,
        *,
        tenant_id: UUID,
        cohort_id: str,
        segment_type: str | None,
        limit: int,
    ) -> list[dict[str, object]]:
        stmt = select(StudentSegmentModel).where(
            StudentSegmentModel.tenant_id == tenant_id,
            StudentSegmentModel.cohort_id == cohort_id,
        )
        if segment_type:
            stmt = stmt.where(StudentSegmentModel.segment_type == segment_type)
        stmt = stmt.order_by(StudentSegmentModel.calculated_at.desc()).limit(limit)
        rows = (await self._session.execute(stmt)).scalars().all()
        return [self._segment_to_dict(row) for row in rows]

    async def list_trends(
        self,
        *,
        tenant_id: UUID,
        cohort_id: str,
        period: str | None,
        limit: int,
    ) -> list[dict[str, object]]:
        stmt = select(CohortTrendModel).where(
            CohortTrendModel.tenant_id == tenant_id,
            CohortTrendModel.cohort_id == cohort_id,
        )
        if period:
            stmt = stmt.where(CohortTrendModel.period == period)
        stmt = stmt.order_by(CohortTrendModel.created_at.desc()).limit(limit)
        rows = (await self._session.execute(stmt)).scalars().all()
        return [self._trend_to_dict(row) for row in rows]

    async def get_admin_metrics(self, *, tenant_id: UUID) -> dict[str, object]:
        since = datetime.now(UTC) - timedelta(days=30)
        total_stmt = select(func.count()).select_from(CohortSnapshotModel).where(
            CohortSnapshotModel.tenant_id == tenant_id
        )
        total = int((await self._session.execute(total_stmt)).scalar_one())
        recent_stmt = select(func.count()).select_from(CohortSnapshotModel).where(
            CohortSnapshotModel.tenant_id == tenant_id,
            CohortSnapshotModel.created_at >= since,
        )
        recent = int((await self._session.execute(recent_stmt)).scalar_one())
        segmented_stmt = select(func.count()).select_from(StudentSegmentModel).where(
            StudentSegmentModel.tenant_id == tenant_id
        )
        segmented = int((await self._session.execute(segmented_stmt)).scalar_one())

        latest_stmt = (
            select(CohortSnapshotModel)
            .where(CohortSnapshotModel.tenant_id == tenant_id)
            .order_by(CohortSnapshotModel.created_at.desc())
            .limit(1)
        )
        latest = (await self._session.execute(latest_stmt)).scalar_one_or_none()
        segment_distribution = dict(latest.segment_counts_json) if latest else {}
        metadata = dict(latest.metadata_json) if latest else {}
        avg_health = float(metadata.get("cohort_health_score", 0.0))

        event_stmt = (
            select(CohortEventModel.event_type, func.count())
            .where(CohortEventModel.tenant_id == tenant_id)
            .group_by(CohortEventModel.event_type)
        )
        event_rows = (await self._session.execute(event_stmt)).all()

        mentor_stmt = (
            select(
                MentorInterventionModel.mentor_id,
                func.count(MentorInterventionModel.id),
                func.avg(InterventionEffectivenessModel.effectiveness_score),
                func.avg(InterventionEffectivenessModel.actual_gain),
            )
            .outerjoin(
                InterventionEffectivenessModel,
                InterventionEffectivenessModel.intervention_id == MentorInterventionModel.id,
            )
            .where(MentorInterventionModel.tenant_id == tenant_id)
            .group_by(MentorInterventionModel.mentor_id)
            .order_by(func.avg(InterventionEffectivenessModel.effectiveness_score).desc())
            .limit(5)
        )
        mentor_rows = (await self._session.execute(mentor_stmt)).all()
        mentor_comparisons = [
            {
                "mentor_id": str(row[0]),
                "student_count": int(row[1] or 0),
                "intervention_success_rate": round(float(row[2] or 0) / 100.0, 4),
                "average_gain": round(float(row[3] or 0), 2),
            }
            for row in mentor_rows
        ]

        return {
            "total_snapshots": total,
            "snapshots_last_30_days": recent,
            "total_students_segmented": segmented,
            "average_cohort_health": round(avg_health, 2),
            "segment_distribution": segment_distribution,
            "top_risk_concepts": list(metadata.get("top_risks", [])),
            "mentor_comparisons": mentor_comparisons,
            "event_counts": [{"event_type": row[0], "count": row[1]} for row in event_rows],
        }

    async def export_rows(self, *, tenant_id: UUID, limit: int) -> list[dict[str, object]]:
        stmt = (
            select(CohortSnapshotModel)
            .where(CohortSnapshotModel.tenant_id == tenant_id)
            .order_by(CohortSnapshotModel.created_at.desc())
            .limit(limit)
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [
            {
                "cohort_id": row.cohort_id,
                "snapshot_date": row.snapshot_date.isoformat(),
                "student_count": row.student_count,
                "avg_readiness": float(row.avg_readiness),
                "avg_forecast": float(row.avg_forecast),
                "risk_count": row.risk_count,
                "created_at": row.created_at.isoformat(),
            }
            for row in rows
        ]

    @staticmethod
    def _snapshot_to_dict(row: CohortSnapshotModel) -> dict[str, object]:
        return {
            "id": row.id,
            "cohort_id": row.cohort_id,
            "exam_id": row.exam_id,
            "snapshot_date": row.snapshot_date,
            "student_count": row.student_count,
            "avg_readiness": float(row.avg_readiness),
            "avg_forecast": float(row.avg_forecast),
            "avg_effectiveness": float(row.avg_effectiveness),
            "risk_count": row.risk_count,
            "segment_counts": dict(row.segment_counts_json),
            "metadata_json": dict(row.metadata_json),
            "created_at": row.created_at,
        }

    @staticmethod
    def _segment_to_dict(row: StudentSegmentModel) -> dict[str, object]:
        return {
            "student_id": row.student_id,
            "segment_type": row.segment_type,
            "segment_score": float(row.segment_score),
            "risk_score": float(row.risk_score),
            "metadata_json": dict(row.metadata_json),
            "calculated_at": row.calculated_at,
        }

    @staticmethod
    def _trend_to_dict(row: CohortTrendModel) -> dict[str, object]:
        return {
            "concept_id": row.concept_id,
            "trend_direction": row.trend_direction,
            "readiness_delta": float(row.readiness_delta),
            "period": row.period,
            "created_at": row.created_at,
        }
