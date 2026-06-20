from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from prepos.application.institution.ports import InstitutionRepositoryPort
from prepos.infrastructure.db.models.cohort_intelligence import CohortSnapshotModel
from prepos.infrastructure.db.models.institution_intelligence import (
    InstitutionEventModel,
    InstitutionInsightModel,
    InstitutionRecommendationModel,
    InstitutionTrendModel,
)
from prepos.infrastructure.db.models.mentor_interventions import (
    InterventionEffectivenessModel,
    MentorInterventionModel,
)


class SqlAlchemyInstitutionRepository(InstitutionRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def load_institution_data(self, *, tenant_id: UUID) -> dict[str, object]:
        latest_by_cohort = await self._latest_snapshots_by_cohort(tenant_id=tenant_id)
        previous_by_cohort = await self._previous_snapshots_by_cohort(tenant_id=tenant_id)

        cohorts: list[dict[str, object]] = []
        concept_counts: dict[str, int] = {}
        total_at_risk = 0
        current_readiness_values: list[float] = []
        current_forecast_values: list[float] = []
        current_ca_values: list[float] = []
        pyq_values: list[float] = []
        previous_readiness_values: list[float] = []
        previous_forecast_values: list[float] = []
        previous_ca_values: list[float] = []

        for cohort_id, snapshot in latest_by_cohort.items():
            metadata = dict(snapshot.metadata_json)
            segment_counts = dict(snapshot.segment_counts_json)
            top_risks = list(metadata.get("top_risks", []))
            for concept in top_risks:
                concept_counts[str(concept)] = concept_counts.get(str(concept), 0) + 1

            at_risk = segment_counts.get("at_risk", 0) + segment_counts.get("critical_risk", 0)
            total_at_risk += at_risk
            readiness = float(snapshot.avg_readiness)
            forecast = float(snapshot.avg_forecast)
            current_readiness_values.append(readiness)
            current_forecast_values.append(forecast)
            ca = float(metadata.get("current_affairs_preparedness", readiness * 0.9))
            pyq = float(metadata.get("pyq_preparedness", readiness * 0.85))
            current_ca_values.append(ca)
            pyq_values.append(pyq)

            previous = previous_by_cohort.get(cohort_id)
            if previous is not None:
                previous_readiness_values.append(float(previous.avg_readiness))
                previous_forecast_values.append(float(previous.avg_forecast))
                prev_meta = dict(previous.metadata_json)
                previous_ca_values.append(
                    float(prev_meta.get("current_affairs_preparedness", float(previous.avg_readiness) * 0.9))
                )

            cohorts.append(
                {
                    "cohort_id": cohort_id,
                    "exam_id": snapshot.exam_id,
                    "student_count": snapshot.student_count,
                    "avg_readiness": readiness,
                    "avg_forecast": forecast,
                    "avg_effectiveness": float(snapshot.avg_effectiveness),
                    "risk_count": snapshot.risk_count,
                    "segment_counts": segment_counts,
                    "top_risks": top_risks,
                    "cohort_health_score": float(metadata.get("cohort_health_score", 0.0)),
                    "current_affairs_preparedness": ca,
                    "pyq_preparedness": pyq,
                    "snapshot_date": snapshot.snapshot_date,
                }
            )

        mentors = await self._mentor_rows(tenant_id=tenant_id)
        intervention_roi = await self._intervention_roi(tenant_id=tenant_id)

        return {
            "cohorts": cohorts,
            "mentors": mentors,
            "concept_cohort_counts": concept_counts,
            "previous_readiness_avg": _avg(previous_readiness_values),
            "current_readiness_avg": _avg(current_readiness_values) or 0.0,
            "previous_forecast_avg": _avg(previous_forecast_values),
            "current_forecast_avg": _avg(current_forecast_values) or 0.0,
            "previous_ca_avg": _avg(previous_ca_values),
            "current_ca_avg": _avg(current_ca_values) or 0.0,
            "intervention_roi": intervention_roi,
            "pyq_gain_signal": _avg(pyq_values) or 0.0,
            "total_at_risk": total_at_risk,
        }

    async def save_insights(
        self,
        *,
        tenant_id: UUID,
        insights: list[dict[str, object]],
        now: datetime,
    ) -> None:
        for insight in insights:
            self._session.add(
                InstitutionInsightModel(
                    id=uuid4(),
                    tenant_id=tenant_id,
                    insight_type=str(insight["insight_type"]),
                    insight_key=str(insight["insight_key"]),
                    title=str(insight["title"]),
                    severity=str(insight["severity"]),
                    evidence_json=list(insight.get("evidence_json") or []),
                    calculation_json=dict(insight.get("calculation_json") or {}),
                    source_metrics_json=dict(insight.get("source_metrics_json") or {}),
                    created_at=now,
                )
            )
        await self._session.flush()

    async def save_recommendations(
        self,
        *,
        tenant_id: UUID,
        recommendations: list[dict[str, object]],
        now: datetime,
    ) -> None:
        for recommendation in recommendations:
            self._session.add(
                InstitutionRecommendationModel(
                    id=uuid4(),
                    tenant_id=tenant_id,
                    recommendation_type=str(recommendation["recommendation_type"]),
                    title=str(recommendation["title"]),
                    expected_impact=recommendation["expected_impact"],  # type: ignore[arg-type]
                    affected_students=int(recommendation["affected_students"]),
                    affected_cohorts_json=list(recommendation.get("affected_cohorts_json") or []),  # type: ignore[arg-type]
                    explanation=str(recommendation["explanation"]),
                    priority_score=recommendation["priority_score"],  # type: ignore[arg-type]
                    metadata_json=dict(recommendation.get("metadata_json") or {}),
                    created_at=now,
                )
            )
        await self._session.flush()

    async def save_trends(
        self,
        *,
        tenant_id: UUID,
        trends: list[dict[str, object]],
        now: datetime,
    ) -> None:
        for trend in trends:
            self._session.add(
                InstitutionTrendModel(
                    id=uuid4(),
                    tenant_id=tenant_id,
                    trend_type=str(trend["trend_type"]),
                    trend_key=str(trend["trend_key"]),
                    trend_direction=str(trend["trend_direction"]),
                    delta_value=trend["delta_value"],  # type: ignore[arg-type]
                    period=str(trend["period"]),
                    metadata_json=dict(trend.get("metadata_json") or {}),
                    created_at=now,
                )
            )
        await self._session.flush()

    async def record_event(
        self,
        *,
        tenant_id: UUID,
        event_type: str,
        metadata_json: dict[str, object],
        now: datetime,
    ) -> UUID:
        event_id = uuid4()
        self._session.add(
            InstitutionEventModel(
                id=event_id,
                tenant_id=tenant_id,
                event_type=event_type,
                metadata_json=metadata_json,
                created_at=now,
            )
        )
        await self._session.flush()
        return event_id

    async def list_insights(
        self,
        *,
        tenant_id: UUID,
        limit: int,
    ) -> list[dict[str, object]]:
        stmt = (
            select(InstitutionInsightModel)
            .where(InstitutionInsightModel.tenant_id == tenant_id)
            .order_by(InstitutionInsightModel.created_at.desc())
            .limit(limit)
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [self._insight_to_dict(row) for row in rows]

    async def list_recommendations(
        self,
        *,
        tenant_id: UUID,
        limit: int,
    ) -> list[dict[str, object]]:
        stmt = (
            select(InstitutionRecommendationModel)
            .where(InstitutionRecommendationModel.tenant_id == tenant_id)
            .order_by(InstitutionRecommendationModel.priority_score.desc())
            .limit(limit)
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [self._recommendation_to_dict(row) for row in rows]

    async def list_trends(
        self,
        *,
        tenant_id: UUID,
        period: str | None,
        limit: int,
    ) -> list[dict[str, object]]:
        stmt = select(InstitutionTrendModel).where(InstitutionTrendModel.tenant_id == tenant_id)
        if period:
            stmt = stmt.where(InstitutionTrendModel.period == period)
        stmt = stmt.order_by(InstitutionTrendModel.created_at.desc()).limit(limit)
        rows = (await self._session.execute(stmt)).scalars().all()
        return [self._trend_to_dict(row) for row in rows]

    async def get_admin_metrics(self, *, tenant_id: UUID) -> dict[str, object]:
        data = await self.load_institution_data(tenant_id=tenant_id)
        event_stmt = (
            select(InstitutionEventModel.event_type, func.count())
            .where(InstitutionEventModel.tenant_id == tenant_id)
            .group_by(InstitutionEventModel.event_type)
        )
        event_rows = (await self._session.execute(event_stmt)).all()
        return {
            **data,
            "event_counts": [{"event_type": row[0], "count": row[1]} for row in event_rows],
        }

    async def export_rows(self, *, tenant_id: UUID, limit: int) -> list[dict[str, object]]:
        insight_stmt = (
            select(InstitutionInsightModel)
            .where(InstitutionInsightModel.tenant_id == tenant_id)
            .order_by(InstitutionInsightModel.created_at.desc())
            .limit(limit)
        )
        insights = (await self._session.execute(insight_stmt)).scalars().all()
        rec_stmt = (
            select(InstitutionRecommendationModel)
            .where(InstitutionRecommendationModel.tenant_id == tenant_id)
            .order_by(InstitutionRecommendationModel.priority_score.desc())
            .limit(limit)
        )
        recommendations = (await self._session.execute(rec_stmt)).scalars().all()
        rows: list[dict[str, object]] = []
        for index, insight in enumerate(insights):
            rec = recommendations[index] if index < len(recommendations) else None
            rows.append(
                {
                    "insight_type": insight.insight_type,
                    "insight_key": insight.insight_key,
                    "title": insight.title,
                    "severity": insight.severity,
                    "created_at": insight.created_at.isoformat(),
                    "recommendation_type": rec.recommendation_type if rec else "",
                    "priority_score": float(rec.priority_score) if rec else "",
                    "expected_impact": float(rec.expected_impact) if rec else "",
                }
            )
        return rows

    async def _latest_snapshots_by_cohort(
        self,
        *,
        tenant_id: UUID,
    ) -> dict[str, CohortSnapshotModel]:
        stmt = (
            select(CohortSnapshotModel)
            .where(CohortSnapshotModel.tenant_id == tenant_id)
            .order_by(CohortSnapshotModel.created_at.desc())
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        mapping: dict[str, CohortSnapshotModel] = {}
        for row in rows:
            if row.cohort_id not in mapping:
                mapping[row.cohort_id] = row
        return mapping

    async def _previous_snapshots_by_cohort(
        self,
        *,
        tenant_id: UUID,
    ) -> dict[str, CohortSnapshotModel]:
        cutoff = date.today() - timedelta(days=30)
        stmt = (
            select(CohortSnapshotModel)
            .where(
                CohortSnapshotModel.tenant_id == tenant_id,
                CohortSnapshotModel.snapshot_date <= cutoff,
            )
            .order_by(CohortSnapshotModel.snapshot_date.desc())
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        mapping: dict[str, CohortSnapshotModel] = {}
        for row in rows:
            if row.cohort_id not in mapping:
                mapping[row.cohort_id] = row
        return mapping

    async def _mentor_rows(self, *, tenant_id: UUID) -> list[dict[str, object]]:
        stmt = (
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
        )
        rows = (await self._session.execute(stmt)).all()
        return [
            {
                "mentor_id": str(row[0]),
                "student_count": int(row[1] or 0),
                "intervention_success_rate": round(float(row[2] or 0) / 100.0, 4),
                "average_gain": round(float(row[3] or 0), 2),
            }
            for row in rows
        ]

    async def _intervention_roi(self, *, tenant_id: UUID) -> float:
        stmt = select(func.avg(InterventionEffectivenessModel.effectiveness_score)).select_from(
            InterventionEffectivenessModel
        ).join(
            MentorInterventionModel,
            MentorInterventionModel.id == InterventionEffectivenessModel.intervention_id,
        ).where(MentorInterventionModel.tenant_id == tenant_id)
        value = (await self._session.execute(stmt)).scalar_one_or_none()
        return round(float(value or 0.0), 2)

    @staticmethod
    def _insight_to_dict(row: InstitutionInsightModel) -> dict[str, object]:
        return {
            "insight_type": row.insight_type,
            "insight_key": row.insight_key,
            "title": row.title,
            "severity": row.severity,
            "evidence_json": list(row.evidence_json) if isinstance(row.evidence_json, list) else row.evidence_json,
            "calculation_json": dict(row.calculation_json),
            "source_metrics_json": dict(row.source_metrics_json),
            "created_at": row.created_at,
        }

    @staticmethod
    def _recommendation_to_dict(row: InstitutionRecommendationModel) -> dict[str, object]:
        return {
            "recommendation_type": row.recommendation_type,
            "title": row.title,
            "expected_impact": float(row.expected_impact),
            "affected_students": row.affected_students,
            "affected_cohorts_json": list(row.affected_cohorts_json),
            "explanation": row.explanation,
            "priority_score": float(row.priority_score),
            "metadata_json": dict(row.metadata_json),
            "created_at": row.created_at,
        }

    @staticmethod
    def _trend_to_dict(row: InstitutionTrendModel) -> dict[str, object]:
        return {
            "trend_type": row.trend_type,
            "trend_key": row.trend_key,
            "trend_direction": row.trend_direction,
            "delta_value": float(row.delta_value),
            "period": row.period,
            "metadata_json": dict(row.metadata_json),
            "created_at": row.created_at,
        }


def _avg(values: list[float]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 2)
