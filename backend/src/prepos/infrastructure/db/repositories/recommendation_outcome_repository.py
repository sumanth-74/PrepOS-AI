from __future__ import annotations

from collections import defaultdict
from datetime import UTC, date, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from prepos.application.recommendations.outcomes.ports import RecommendationOutcomeRepositoryPort
from prepos.infrastructure.db.models.recommendation_analytics import RecommendationEventModel
from prepos.infrastructure.db.models.recommendation_outcomes import (
    RecommendationEffectivenessMetricModel,
    RecommendationOutcomeModel,
)


class SqlAlchemyRecommendationOutcomeRepository(RecommendationOutcomeRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_latest_shown_event(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        concept_id: str,
    ) -> dict[str, object] | None:
        stmt = (
            select(RecommendationEventModel)
            .where(
                RecommendationEventModel.tenant_id == tenant_id,
                RecommendationEventModel.student_id == student_id,
                RecommendationEventModel.concept_id == concept_id,
                RecommendationEventModel.event_type == "recommendation_shown",
            )
            .order_by(RecommendationEventModel.created_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        event = result.scalar_one_or_none()
        return _event_to_dict(event) if event else None

    async def get_pending_shown_events(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        as_of: datetime,
        min_age_days: int,
    ) -> list[dict[str, object]]:
        cutoff = as_of - timedelta(days=min_age_days)
        stmt = select(RecommendationEventModel).where(
            RecommendationEventModel.tenant_id == tenant_id,
            RecommendationEventModel.student_id == student_id,
            RecommendationEventModel.event_type == "recommendation_shown",
            RecommendationEventModel.created_at <= cutoff,
        )
        result = await self._session.execute(stmt)
        events = list(result.scalars())
        pending: list[dict[str, object]] = []
        for event in events:
            if event.id is None:
                continue
            if await self.outcome_exists_for_event(recommendation_event_id=event.id):
                continue
            pending.append(_event_to_dict(event))
        return pending

    async def outcome_exists_for_event(self, *, recommendation_event_id: UUID) -> bool:
        stmt = select(RecommendationOutcomeModel.id).where(
            RecommendationOutcomeModel.recommendation_event_id == recommendation_event_id
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def create_outcome(
        self,
        *,
        recommendation_event_id: UUID,
        tenant_id: UUID,
        user_id: UUID | None,
        student_id: UUID | None,
        concept_id: str,
        readiness_before: float | None,
        readiness_after: float | None,
        forecast_before: float | None,
        forecast_after: float | None,
        weakness_before: float | None,
        weakness_after: float | None,
        study_minutes: int,
        predicted_gain: float | None,
        actual_gain: float | None,
        effectiveness_score: float | None,
        status: str,
        created_at: datetime,
    ) -> UUID:
        outcome_id = uuid4()
        self._session.add(
            RecommendationOutcomeModel(
                id=outcome_id,
                recommendation_event_id=recommendation_event_id,
                tenant_id=tenant_id,
                user_id=user_id,
                student_id=student_id,
                concept_id=concept_id,
                readiness_before=readiness_before,
                readiness_after=readiness_after,
                forecast_before=forecast_before,
                forecast_after=forecast_after,
                weakness_before=weakness_before,
                weakness_after=weakness_after,
                study_minutes=study_minutes,
                predicted_gain=predicted_gain,
                actual_gain=actual_gain,
                effectiveness_score=effectiveness_score,
                status=status,
                created_at=created_at,
            )
        )
        await self._session.flush()
        return outcome_id

    async def list_outcomes(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID | None = None,
        user_id: UUID | None = None,
        concept_id: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, object]]:
        filters = [RecommendationOutcomeModel.tenant_id == tenant_id]
        if student_id is not None:
            filters.append(RecommendationOutcomeModel.student_id == student_id)
        if user_id is not None:
            filters.append(RecommendationOutcomeModel.user_id == user_id)
        if concept_id is not None:
            filters.append(RecommendationOutcomeModel.concept_id == concept_id)
        stmt = (
            select(RecommendationOutcomeModel)
            .where(and_(*filters))
            .order_by(RecommendationOutcomeModel.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [_outcome_to_dict(row) for row in result.scalars()]

    async def get_outcome_by_concept(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        concept_id: str,
    ) -> dict[str, object] | None:
        stmt = (
            select(RecommendationOutcomeModel)
            .where(
                RecommendationOutcomeModel.tenant_id == tenant_id,
                RecommendationOutcomeModel.student_id == student_id,
                RecommendationOutcomeModel.concept_id == concept_id,
            )
            .order_by(RecommendationOutcomeModel.created_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return _outcome_to_dict(row) if row else None

    async def get_concept_effectiveness_stats(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID | None = None,
        concept_id: str | None = None,
        since: datetime | None = None,
    ) -> list[dict[str, object]]:
        filters = [RecommendationOutcomeModel.tenant_id == tenant_id]
        if student_id is not None:
            filters.append(RecommendationOutcomeModel.student_id == student_id)
        if concept_id is not None:
            filters.append(RecommendationOutcomeModel.concept_id == concept_id)
        if since is not None:
            filters.append(RecommendationOutcomeModel.created_at >= since)
        stmt = select(RecommendationOutcomeModel).where(and_(*filters))
        result = await self._session.execute(stmt)
        rows = list(result.scalars())
        grouped: dict[str, list[RecommendationOutcomeModel]] = defaultdict(list)
        for row in rows:
            grouped[row.concept_id].append(row)

        stats: list[dict[str, object]] = []
        for concept, items in grouped.items():
            predicted = sum(float(item.predicted_gain or 0) for item in items) / len(items)
            actual = sum(float(item.actual_gain or 0) for item in items) / len(items)
            effectiveness = sum(float(item.effectiveness_score or 0) for item in items) / len(items)
            success_items = [item for item in items if item.status == "successful"]
            status = "successful" if len(success_items) >= len(items) / 2 else (
                "partial" if effectiveness >= 0.5 else "failed"
            )
            stats.append(
                {
                    "concept_id": concept,
                    "predicted_gain": round(predicted, 2),
                    "actual_gain": round(actual, 2),
                    "effectiveness_score": round(effectiveness, 2),
                    "status": status,
                    "outcome_count": len(items),
                }
            )
        stats.sort(key=lambda item: float(item["effectiveness_score"]), reverse=True)
        return stats

    async def upsert_daily_metric(
        self,
        *,
        tenant_id: UUID,
        metric_date: date,
        concept_id: str,
        predicted_gain: float,
        actual_gain: float,
        effectiveness_score: float,
        is_completion: bool,
        now: datetime,
    ) -> None:
        stmt = select(RecommendationEffectivenessMetricModel).where(
            RecommendationEffectivenessMetricModel.tenant_id == tenant_id,
            RecommendationEffectivenessMetricModel.metric_date == metric_date,
            RecommendationEffectivenessMetricModel.concept_id == concept_id,
        )
        result = await self._session.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing is None:
            self._session.add(
                RecommendationEffectivenessMetricModel(
                    id=uuid4(),
                    tenant_id=tenant_id,
                    metric_date=metric_date,
                    concept_id=concept_id,
                    recommendation_count=1,
                    completion_count=1 if is_completion else 0,
                    average_predicted_gain=predicted_gain,
                    average_actual_gain=actual_gain,
                    average_effectiveness=effectiveness_score,
                    created_at=now,
                    updated_at=now,
                )
            )
        else:
            count = existing.completion_count + (1 if is_completion else 0)
            existing.completion_count = count
            existing.recommendation_count = max(existing.recommendation_count, count)
            existing.average_predicted_gain = round(
                ((float(existing.average_predicted_gain) * (count - 1)) + predicted_gain) / count,
                2,
            )
            existing.average_actual_gain = round(
                ((float(existing.average_actual_gain) * (count - 1)) + actual_gain) / count,
                2,
            )
            existing.average_effectiveness = round(
                ((float(existing.average_effectiveness) * (count - 1)) + effectiveness_score) / count,
                2,
            )
            existing.updated_at = now
        await self._session.flush()

    async def get_admin_effectiveness_metrics(
        self,
        *,
        tenant_id: UUID,
        since: datetime,
    ) -> dict[str, object]:
        outcomes_stmt = select(RecommendationOutcomeModel).where(
            RecommendationOutcomeModel.tenant_id == tenant_id,
            RecommendationOutcomeModel.created_at >= since,
        )
        outcomes_result = await self._session.execute(outcomes_stmt)
        outcomes = list(outcomes_result.scalars())

        shown_stmt = select(RecommendationEventModel).where(
            RecommendationEventModel.tenant_id == tenant_id,
            RecommendationEventModel.created_at >= since,
            RecommendationEventModel.event_type == "recommendation_shown",
        )
        shown_result = await self._session.execute(shown_stmt)
        shown_count = len(list(shown_result.scalars()))

        if not outcomes:
            return {
                "average_effectiveness": 0.0,
                "average_actual_gain": 0.0,
                "completion_rate": 0.0,
                "success_rate": 0.0,
                "concept_rankings": [],
                "readiness_uplift_trend": [],
                "forecast_uplift_trend": [],
            }

        avg_effectiveness = sum(float(item.effectiveness_score or 0) for item in outcomes) / len(outcomes)
        avg_actual = sum(float(item.actual_gain or 0) for item in outcomes) / len(outcomes)
        success_count = sum(1 for item in outcomes if item.status == "successful")
        completion_rate = len(outcomes) / shown_count if shown_count else 0.0
        success_rate = success_count / len(outcomes)

        concept_rankings = await self.get_concept_effectiveness_stats(tenant_id=tenant_id, since=since)

        readiness_by_date: dict[str, list[float]] = defaultdict(list)
        forecast_by_date: dict[str, list[float]] = defaultdict(list)
        for item in outcomes:
            day = item.created_at.date().isoformat()
            if item.readiness_before is not None and item.readiness_after is not None:
                readiness_by_date[day].append(float(item.readiness_after) - float(item.readiness_before))
            if item.forecast_before is not None and item.forecast_after is not None:
                forecast_by_date[day].append(float(item.forecast_after) - float(item.forecast_before))

        readiness_trend = [
            {"date": day, "average_uplift": round(sum(values) / len(values), 2)}
            for day, values in sorted(readiness_by_date.items())
        ]
        forecast_trend = [
            {"date": day, "average_uplift": round(sum(values) / len(values), 2)}
            for day, values in sorted(forecast_by_date.items())
        ]

        return {
            "average_effectiveness": round(avg_effectiveness, 2),
            "average_actual_gain": round(avg_actual, 2),
            "completion_rate": round(completion_rate, 4),
            "success_rate": round(success_rate, 4),
            "concept_rankings": concept_rankings,
            "readiness_uplift_trend": readiness_trend,
            "forecast_uplift_trend": forecast_trend,
        }


def _event_to_dict(event: RecommendationEventModel) -> dict[str, object]:
    return {
        "id": event.id,
        "tenant_id": event.tenant_id,
        "user_id": event.user_id,
        "student_id": event.student_id,
        "concept_id": event.concept_id,
        "estimated_gain": float(event.estimated_gain) if event.estimated_gain is not None else None,
        "metadata_json": dict(event.metadata_json or {}),
        "created_at": event.created_at,
    }


def _outcome_to_dict(row: RecommendationOutcomeModel) -> dict[str, object]:
    return {
        "id": row.id,
        "recommendation_event_id": row.recommendation_event_id,
        "tenant_id": row.tenant_id,
        "user_id": row.user_id,
        "student_id": row.student_id,
        "concept_id": row.concept_id,
        "readiness_before": float(row.readiness_before) if row.readiness_before is not None else None,
        "readiness_after": float(row.readiness_after) if row.readiness_after is not None else None,
        "forecast_before": float(row.forecast_before) if row.forecast_before is not None else None,
        "forecast_after": float(row.forecast_after) if row.forecast_after is not None else None,
        "weakness_before": float(row.weakness_before) if row.weakness_before is not None else None,
        "weakness_after": float(row.weakness_after) if row.weakness_after is not None else None,
        "study_minutes": row.study_minutes,
        "predicted_gain": float(row.predicted_gain) if row.predicted_gain is not None else None,
        "actual_gain": float(row.actual_gain) if row.actual_gain is not None else None,
        "effectiveness_score": float(row.effectiveness_score) if row.effectiveness_score is not None else None,
        "status": row.status,
        "created_at": row.created_at,
    }
