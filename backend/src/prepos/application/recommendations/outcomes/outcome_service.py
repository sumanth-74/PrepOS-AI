from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

import structlog

from prepos.application.learning_graph.read_services import LearningGraphReadService
from prepos.application.recommendations.outcomes.effectiveness_calculator import (
    calculate_actual_gain,
    calculate_effectiveness_score,
    outcome_status,
)
from prepos.application.recommendations.outcomes.outcome_analytics import (
    OUTCOME_EVALUATION_DAYS,
    SIGNIFICANT_READINESS_CHANGE,
    build_outcome_list,
    map_outcome_row,
)
from prepos.application.recommendations.outcomes.outcome_models import RecommendationOutcomeResponse
from prepos.application.recommendations.outcomes.ports import RecommendationOutcomeRepositoryPort
from prepos.application.recommendations.ports import RecommendationAnalyticsRepositoryPort
from prepos.application.twin.twin_read_service import TwinReadService

logger = structlog.get_logger(__name__)


class RecommendationOutcomeService:
    def __init__(
        self,
        *,
        outcome_repository: RecommendationOutcomeRepositoryPort,
        analytics_repository: RecommendationAnalyticsRepositoryPort | None = None,
        twin_read_service: TwinReadService,
        learning_graph_read_service: LearningGraphReadService,
    ) -> None:
        self._outcome_repository = outcome_repository
        self._analytics_repository = analytics_repository
        self._twin_read_service = twin_read_service
        self._learning_graph_read_service = learning_graph_read_service

    async def evaluate_on_completion(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID | None,
        student_id: UUID,
        concept_id: str,
        exam_id: str | None,
        study_minutes: int = 0,
    ) -> RecommendationOutcomeResponse | None:
        await self.evaluate_pending(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
        )
        return await self._evaluate_outcome(
            tenant_id=tenant_id,
            user_id=user_id,
            student_id=student_id,
            concept_id=concept_id,
            exam_id=exam_id,
            study_minutes=study_minutes,
            trigger="completion",
        )

    async def evaluate_pending(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str | None,
    ) -> list[RecommendationOutcomeResponse]:
        now = datetime.now(UTC)
        pending = await self._outcome_repository.get_pending_shown_events(
            tenant_id=tenant_id,
            student_id=student_id,
            as_of=now,
            min_age_days=OUTCOME_EVALUATION_DAYS,
        )
        results: list[RecommendationOutcomeResponse] = []
        dashboard = await self._twin_read_service.get_dashboard(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
        )
        current_readiness = _to_float(dashboard.readiness_score)

        for event in pending:
            metadata = dict(event.get("metadata_json") or {})
            before_readiness = _to_float(metadata.get("readiness_before"))
            if before_readiness is None or current_readiness is None:
                continue
            if abs(current_readiness - before_readiness) < SIGNIFICANT_READINESS_CHANGE:
                continue
            concept_id = str(event["concept_id"])
            outcome = await self._evaluate_outcome(
                tenant_id=tenant_id,
                user_id=UUID(str(event["user_id"])) if event.get("user_id") else None,
                student_id=student_id,
                concept_id=concept_id,
                exam_id=exam_id,
                study_minutes=int(metadata.get("study_minutes") or 0),
                trigger="readiness_change",
            )
            if outcome is not None:
                results.append(outcome)
        return results

    async def list_outcomes(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID | None = None,
        user_id: UUID | None = None,
        concept_id: str | None = None,
        limit: int = 50,
    ):
        rows = await self._outcome_repository.list_outcomes(
            tenant_id=tenant_id,
            student_id=student_id,
            user_id=user_id,
            concept_id=concept_id,
            limit=limit,
        )
        return build_outcome_list(rows)

    async def get_outcome_for_concept(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        concept_id: str,
    ) -> RecommendationOutcomeResponse | None:
        row = await self._outcome_repository.get_outcome_by_concept(
            tenant_id=tenant_id,
            student_id=student_id,
            concept_id=concept_id,
        )
        if row is None:
            return None
        return map_outcome_row(row)

    async def get_historical_effectiveness(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        concept_id: str,
    ) -> tuple[float, float]:
        stats = await self._outcome_repository.get_concept_effectiveness_stats(
            tenant_id=tenant_id,
            student_id=student_id,
            concept_id=concept_id,
        )
        if not stats:
            return 0.0, 0.0
        row = stats[0]
        return float(row["effectiveness_score"]), float(row["actual_gain"])

    async def _evaluate_outcome(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID | None,
        student_id: UUID,
        concept_id: str,
        exam_id: str | None,
        study_minutes: int,
        trigger: str,
    ) -> RecommendationOutcomeResponse | None:
        shown_event = await self._outcome_repository.get_latest_shown_event(
            tenant_id=tenant_id,
            student_id=student_id,
            concept_id=concept_id,
        )
        if shown_event is None:
            return None

        event_id = UUID(str(shown_event["id"]))
        if await self._outcome_repository.outcome_exists_for_event(recommendation_event_id=event_id):
            return None

        metadata = dict(shown_event.get("metadata_json") or {})
        predicted_gain = float(shown_event.get("estimated_gain") or metadata.get("predicted_gain") or 0)
        readiness_before = _to_float(metadata.get("readiness_before"))
        forecast_before = _to_float(metadata.get("forecast_before"))
        weakness_before = _to_float(metadata.get("weakness_before"))

        resolved_exam_id = exam_id or str(metadata.get("exam_id") or "upsc_cse")
        dashboard = await self._twin_read_service.get_dashboard(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=resolved_exam_id,
        )
        weaknesses = await self._learning_graph_read_service.get_weaknesses(
            tenant_id=tenant_id,
            student_id=student_id,
            limit=50,
        )
        weakness = next((item for item in weaknesses.weaknesses if item.concept_id == concept_id), None)

        readiness_after = _to_float(dashboard.readiness_score)
        forecast_after = _to_float(dashboard.projected_readiness)
        weakness_after = _to_float(weakness.weakness_score if weakness else None)

        if readiness_before is None:
            readiness_before = readiness_after
        if forecast_before is None:
            forecast_before = forecast_after
        if weakness_before is None:
            weakness_before = weakness_after

        actual_gain = calculate_actual_gain(
            readiness_before=readiness_before or 0.0,
            readiness_after=readiness_after or 0.0,
        )
        effectiveness = calculate_effectiveness_score(
            actual_gain=actual_gain,
            predicted_gain=predicted_gain,
        )
        status = outcome_status(effectiveness_score=effectiveness, actual_gain=actual_gain)
        now = datetime.now(UTC)

        logger.info(
            "recommendation_outcome_started",
            tenant_id=str(tenant_id),
            user_id=str(user_id) if user_id else None,
            concept_id=concept_id,
            predicted_gain=predicted_gain,
            trigger=trigger,
        )

        outcome_id = await self._outcome_repository.create_outcome(
            recommendation_event_id=event_id,
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
            effectiveness_score=effectiveness,
            status=status,
            created_at=now,
        )

        await self._outcome_repository.upsert_daily_metric(
            tenant_id=tenant_id,
            metric_date=now.date(),
            concept_id=concept_id,
            predicted_gain=predicted_gain,
            actual_gain=actual_gain,
            effectiveness_score=effectiveness,
            is_completion=True,
            now=now,
        )

        if self._analytics_repository is not None:
            event_type = "recommendation_success" if status == "successful" else "recommendation_failure"
            await self._analytics_repository.record_event(
                tenant_id=tenant_id,
                user_id=user_id,
                student_id=student_id,
                event_type="recommendation_outcome_generated",
                concept_id=concept_id,
                impact_score=None,
                estimated_gain=predicted_gain,
                readiness_gain_after=actual_gain,
                metadata_json={
                    "effectiveness_score": effectiveness,
                    "status": status,
                    "trigger": trigger,
                },
                created_at=now,
            )
            await self._analytics_repository.record_event(
                tenant_id=tenant_id,
                user_id=user_id,
                student_id=student_id,
                event_type=event_type,
                concept_id=concept_id,
                impact_score=effectiveness,
                estimated_gain=predicted_gain,
                readiness_gain_after=actual_gain,
                metadata_json={"status": status},
                created_at=now,
            )

        logger.info(
            "recommendation_outcome_completed",
            tenant_id=str(tenant_id),
            user_id=str(user_id) if user_id else None,
            concept_id=concept_id,
            predicted_gain=predicted_gain,
            actual_gain=actual_gain,
            effectiveness_score=effectiveness,
        )
        logger.info(
            "recommendation_effectiveness_calculated",
            tenant_id=str(tenant_id),
            user_id=str(user_id) if user_id else None,
            concept_id=concept_id,
            predicted_gain=predicted_gain,
            actual_gain=actual_gain,
            effectiveness_score=effectiveness,
        )
        if status == "successful":
            logger.info(
                "recommendation_success",
                tenant_id=str(tenant_id),
                user_id=str(user_id) if user_id else None,
                concept_id=concept_id,
                predicted_gain=predicted_gain,
                actual_gain=actual_gain,
                effectiveness_score=effectiveness,
            )
        else:
            logger.info(
                "recommendation_failure",
                tenant_id=str(tenant_id),
                user_id=str(user_id) if user_id else None,
                concept_id=concept_id,
                predicted_gain=predicted_gain,
                actual_gain=actual_gain,
                effectiveness_score=effectiveness,
            )

        row = {
            "id": outcome_id,
            "recommendation_event_id": event_id,
            "concept_id": concept_id,
            "predicted_gain": predicted_gain,
            "actual_gain": actual_gain,
            "effectiveness_score": effectiveness,
            "status": status,
            "readiness_before": readiness_before,
            "readiness_after": readiness_after,
            "forecast_before": forecast_before,
            "forecast_after": forecast_after,
            "weakness_before": weakness_before,
            "weakness_after": weakness_after,
            "study_minutes": study_minutes,
            "created_at": now,
        }
        return map_outcome_row(row)


def _to_float(value: Decimal | float | int | str | None) -> float | None:
    if value is None:
        return None
    return float(value)
