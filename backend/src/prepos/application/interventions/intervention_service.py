from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

import structlog

from prepos.application.forecasting.forecast_service import GoalForecastingService
from prepos.application.interventions.intervention_analytics import InterventionAnalyticsService
from prepos.application.interventions.intervention_effectiveness import (
    classify_intervention_outcome,
    compute_actual_gain,
    compute_effectiveness_score,
)
from prepos.application.interventions.intervention_explainer import explain_intervention
from prepos.application.interventions.intervention_models import (
    InterventionAdminResponse,
    InterventionExplainResponse,
    InterventionHistoryEntry,
    InterventionHistoryResponse,
    InterventionRecordResponse,
    MentorInterventionQueueItem,
    MentorInterventionQueueResponse,
    RecommendedInterventionItem,
    StudentInterventionResponse,
)
from prepos.application.interventions.intervention_optimizer import optimize_interventions
from prepos.application.interventions.ports import InterventionRepositoryPort
from prepos.application.memory.memory_service import CoachingMemoryService
from prepos.application.planning.planning_service import AdaptivePlanningService
from prepos.application.recommendations.recommendation_engine import format_concept_name
from prepos.application.recommendations.recommendation_service import LearningRecommendationService
from prepos.application.twin.twin_read_service import TwinReadService

logger = structlog.get_logger(__name__)


class MentorInterventionService:
    def __init__(
        self,
        *,
        repository: InterventionRepositoryPort,
        twin_read_service: TwinReadService,
        recommendation_service: LearningRecommendationService,
        memory_service: CoachingMemoryService,
        planning_service: AdaptivePlanningService,
        forecasting_service: GoalForecastingService,
        analytics_service: InterventionAnalyticsService | None = None,
    ) -> None:
        self._repository = repository
        self._twin_read_service = twin_read_service
        self._recommendation_service = recommendation_service
        self._memory_service = memory_service
        self._planning_service = planning_service
        self._forecasting_service = forecasting_service
        self._analytics = analytics_service or InterventionAnalyticsService(repository=repository)

    async def generate_recommendations(
        self,
        *,
        tenant_id: UUID,
        mentor_id: UUID,
        student_id: UUID,
        student_user_id: UUID,
        exam_id: str,
    ) -> StudentInterventionResponse:
        resolved_exam = exam_id or "upsc_cse"
        now = datetime.now(UTC)
        inputs = await self._build_optimizer_inputs(
            tenant_id=tenant_id,
            student_id=student_id,
            student_user_id=student_user_id,
            exam_id=resolved_exam,
        )
        ranked = optimize_interventions(
            concept_candidates=inputs["concept_candidates"],
            forecast_risk=float(inputs["forecast_risk"]),
            memory_signal=float(inputs["memory_signal"]),
            limit=5,
        )
        recommendation_rows = [
            {
                "intervention_type": item.intervention_type,
                "concept_id": item.concept_id,
                "recommendation_reason": item.reason,
                "impact_score": item.impact_score,
                "confidence": item.confidence,
                "predicted_gain": item.predicted_gain,
            }
            for item in ranked
        ]
        await self._repository.create_recommendations(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=resolved_exam,
            recommendations=recommendation_rows,
            now=now,
        )
        if ranked:
            top = ranked[0]
            await self._repository.create_intervention(
                tenant_id=tenant_id,
                mentor_id=mentor_id,
                student_id=student_id,
                exam_id=resolved_exam,
                intervention_type=top.intervention_type,
                concept_id=top.concept_id,
                reason=top.reason,
                predicted_gain=top.predicted_gain,
                priority_score=top.priority_score,
                status="pending",
                metadata_json={
                    "readiness_before": inputs.get("current_readiness", 0.0),
                    "forecast_improvement": top.forecast_improvement,
                    "score_breakdown": top.score_breakdown.model_dump(),
                },
                now=now,
            )
        active = await self._repository.list_student_interventions(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=resolved_exam,
            limit=20,
        )
        logger.info(
            "intervention_generated",
            tenant_id=str(tenant_id),
            mentor_id=str(mentor_id),
            student_id=str(student_id),
            priority_score=ranked[0].priority_score if ranked else 0,
            predicted_gain=ranked[0].predicted_gain if ranked else 0,
            concept_id=ranked[0].concept_id if ranked else None,
        )
        return StudentInterventionResponse(
            student_id=student_id,
            exam_id=resolved_exam,
            current_readiness=inputs.get("current_readiness"),  # type: ignore[arg-type]
            forecast_status=inputs.get("forecast_status"),  # type: ignore[arg-type]
            recommended_interventions=[self._map_ranked(item) for item in ranked],
            active_interventions=[self._map_intervention(row) for row in active if row["status"] in {"pending", "in_progress"}],
            generated_at=now,
        )

    async def get_student_interventions(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        student_user_id: UUID,
        exam_id: str,
    ) -> StudentInterventionResponse:
        resolved_exam = exam_id or "upsc_cse"
        recommendations = await self._repository.list_student_recommendations(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=resolved_exam,
            limit=5,
        )
        if not recommendations:
            return await self.generate_recommendations(
                tenant_id=tenant_id,
                mentor_id=student_user_id,
                student_id=student_id,
                student_user_id=student_user_id,
                exam_id=resolved_exam,
            )
        active = await self._repository.list_student_interventions(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=resolved_exam,
            limit=20,
        )
        dashboard = await self._twin_read_service.get_dashboard(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=resolved_exam,
        )
        forecast = await self._forecasting_service.get_current_forecast(
            tenant_id=tenant_id,
            user_id=student_user_id,
            exam_id=resolved_exam,
        )
        return StudentInterventionResponse(
            student_id=student_id,
            exam_id=resolved_exam,
            current_readiness=float(dashboard.readiness_score) if dashboard.readiness_score is not None else None,
            forecast_status=forecast.forecast_status if forecast else None,
            recommended_interventions=[self._map_recommendation(row) for row in recommendations],
            active_interventions=[self._map_intervention(row) for row in active if row["status"] in {"pending", "in_progress"}],
            generated_at=datetime.now(UTC),
        )

    async def execute_intervention(
        self,
        *,
        tenant_id: UUID,
        mentor_id: UUID,
        intervention_id: UUID,
    ) -> InterventionRecordResponse:
        row = await self._repository.get_intervention(tenant_id=tenant_id, intervention_id=intervention_id)
        if row is None:
            raise ValueError("Intervention not found.")
        await self._repository.update_intervention_status(
            tenant_id=tenant_id,
            intervention_id=intervention_id,
            status="in_progress",
        )
        logger.info(
            "intervention_executed",
            tenant_id=str(tenant_id),
            mentor_id=str(mentor_id),
            student_id=str(row["student_id"]),
            concept_id=row.get("concept_id"),
            priority_score=row["priority_score"],
            predicted_gain=row["predicted_gain"],
        )
        updated = await self._repository.get_intervention(tenant_id=tenant_id, intervention_id=intervention_id)
        assert updated is not None
        return self._map_intervention(updated)

    async def complete_intervention(
        self,
        *,
        tenant_id: UUID,
        mentor_id: UUID,
        intervention_id: UUID,
    ) -> InterventionHistoryEntry:
        row = await self._repository.get_intervention(tenant_id=tenant_id, intervention_id=intervention_id)
        if row is None:
            raise ValueError("Intervention not found.")
        student_id = row["student_id"]  # type: ignore[assignment]
        dashboard = await self._twin_read_service.get_dashboard(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=str(row["exam_id"]),
        )
        readiness_after = float(dashboard.readiness_score or 0.0)
        metadata = row.get("metadata_json") or {}
        readiness_before = float(metadata.get("readiness_before", readiness_after))
        actual_gain = compute_actual_gain(readiness_before=readiness_before, readiness_after=readiness_after)
        effectiveness = compute_effectiveness_score(
            predicted_gain=float(row["predicted_gain"]),
            actual_gain=actual_gain,
        )
        now = datetime.now(UTC)
        await self._repository.update_intervention_status(
            tenant_id=tenant_id,
            intervention_id=intervention_id,
            status="completed",
        )
        evaluated_id = await self._repository.record_effectiveness(
            intervention_id=intervention_id,
            readiness_before=readiness_before,
            readiness_after=readiness_after,
            actual_gain=actual_gain,
            effectiveness_score=effectiveness,
            now=now,
        )
        outcome = classify_intervention_outcome(effectiveness)
        logger.info(
            "intervention_completed",
            tenant_id=str(tenant_id),
            mentor_id=str(mentor_id),
            student_id=str(student_id),
            concept_id=row.get("concept_id"),
            priority_score=row["priority_score"],
            predicted_gain=row["predicted_gain"],
            actual_gain=actual_gain,
        )
        logger.info(
            "intervention_effectiveness_calculated",
            tenant_id=str(tenant_id),
            mentor_id=str(mentor_id),
            student_id=str(student_id),
            effectiveness_score=effectiveness,
            event_type=outcome,
            intervention_id=str(intervention_id),
            evaluated_id=str(evaluated_id),
        )
        return InterventionHistoryEntry(
            intervention_id=intervention_id,
            intervention_type=str(row["intervention_type"]),
            concept_id=row.get("concept_id"),  # type: ignore[arg-type]
            concept=format_concept_name(str(row["concept_id"])) if row.get("concept_id") else None,
            status="completed",
            predicted_gain=float(row["predicted_gain"]),
            actual_gain=actual_gain,
            effectiveness_score=effectiveness,
            created_at=row["created_at"],  # type: ignore[arg-type]
            evaluated_at=now,
        )

    async def assign_top_intervention(
        self,
        *,
        tenant_id: UUID,
        mentor_id: UUID,
        student_id: UUID,
        student_user_id: UUID,
        exam_id: str,
    ) -> InterventionRecordResponse:
        bundle = await self.generate_recommendations(
            tenant_id=tenant_id,
            mentor_id=mentor_id,
            student_id=student_id,
            student_user_id=student_user_id,
            exam_id=exam_id,
        )
        if not bundle.recommended_interventions:
            raise ValueError("No interventions to assign.")
        top = bundle.recommended_interventions[0]
        dashboard = await self._twin_read_service.get_dashboard(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
        )
        now = datetime.now(UTC)
        intervention_id = await self._repository.create_intervention(
            tenant_id=tenant_id,
            mentor_id=mentor_id,
            student_id=student_id,
            exam_id=exam_id,
            intervention_type=top.intervention_type,
            concept_id=top.concept_id,
            reason=top.reason,
            predicted_gain=top.predicted_gain,
            priority_score=top.priority_score,
            status="pending",
            metadata_json={"readiness_before": float(dashboard.readiness_score or 0.0)},
            now=now,
        )
        row = await self._repository.get_intervention(tenant_id=tenant_id, intervention_id=intervention_id)
        assert row is not None
        return self._map_intervention(row)

    async def explain_intervention(
        self,
        *,
        tenant_id: UUID,
        intervention_id: UUID,
    ) -> InterventionExplainResponse:
        row = await self._repository.get_intervention(tenant_id=tenant_id, intervention_id=intervention_id)
        if row is None:
            raise ValueError("Intervention not found.")
        metadata = row.get("metadata_json") or {}
        breakdown_data = metadata.get("score_breakdown") or {}
        from prepos.application.interventions.intervention_models import InterventionScoreBreakdown

        breakdown = InterventionScoreBreakdown(
            forecast_risk=float(breakdown_data.get("forecast_risk", 50)),
            weakness=float(breakdown_data.get("weakness", 50)),
            historical_failure=float(breakdown_data.get("historical_failure", 30)),
            pyq_importance=float(breakdown_data.get("pyq_importance", 40)),
            memory_signal=float(breakdown_data.get("memory_signal", 35)),
            priority_score=float(row["priority_score"]),
        )
        concept = format_concept_name(str(row["concept_id"])) if row.get("concept_id") else None
        forecast_improvement = float(metadata.get("forecast_improvement", row["predicted_gain"]))
        explanations = explain_intervention(
            intervention_type=str(row["intervention_type"]),
            concept=concept,
            reason=str(row["reason"]),
            predicted_gain=float(row["predicted_gain"]),
            priority_score=float(row["priority_score"]),
            score_breakdown=breakdown,
            forecast_improvement=forecast_improvement,
        )
        return InterventionExplainResponse(
            intervention_id=intervention_id,
            intervention_type=str(row["intervention_type"]),
            concept_id=row.get("concept_id"),  # type: ignore[arg-type]
            concept=concept,
            reason=str(row["reason"]),
            predicted_gain=float(row["predicted_gain"]),
            priority_score=float(row["priority_score"]),
            score_breakdown=breakdown,
            explanations=explanations,
        )

    async def get_student_history(
        self,
        *,
        tenant_id: UUID,
        student_user_id: UUID,
        exam_id: str | None,
        limit: int = 20,
    ) -> InterventionHistoryResponse:
        rows = await self._repository.list_student_history(
            tenant_id=tenant_id,
            student_user_id=student_user_id,
            exam_id=exam_id,
            limit=limit,
        )
        entries = [
            InterventionHistoryEntry(
                intervention_id=row["intervention_id"],  # type: ignore[arg-type]
                intervention_type=str(row["intervention_type"]),
                concept_id=row.get("concept_id"),  # type: ignore[arg-type]
                concept=format_concept_name(str(row["concept_id"])) if row.get("concept_id") else None,
                status=str(row["status"]),
                predicted_gain=float(row["predicted_gain"]),
                actual_gain=float(row["actual_gain"]) if row.get("actual_gain") is not None else None,
                effectiveness_score=float(row["effectiveness_score"]) if row.get("effectiveness_score") is not None else None,
                created_at=row["created_at"],  # type: ignore[arg-type]
                evaluated_at=row.get("evaluated_at"),  # type: ignore[arg-type]
            )
            for row in rows
        ]
        return InterventionHistoryResponse(interventions=entries, total=len(entries))

    async def get_mentor_queue(
        self,
        *,
        tenant_id: UUID,
        mentor_id: UUID,
        limit: int = 20,
    ) -> MentorInterventionQueueResponse:
        rows = await self._repository.list_mentor_queue(
            tenant_id=tenant_id,
            mentor_id=mentor_id,
            limit=limit,
        )
        items = [
            MentorInterventionQueueItem(
                student_id=row["student_id"],  # type: ignore[arg-type]
                exam_id=str(row["exam_id"]),
                top_intervention_type=str(row["intervention_type"]),
                top_concept=format_concept_name(str(row["concept_id"])) if row.get("concept_id") else None,
                priority_score=float(row["priority_score"]),
                predicted_gain=float(row["predicted_gain"]),
                forecast_status=row.get("forecast_status"),  # type: ignore[arg-type]
                reason=str(row["reason"]),
            )
            for row in rows
        ]
        return MentorInterventionQueueResponse(items=items, total=len(items))

    async def get_admin_dashboard(self, *, tenant_id: UUID) -> InterventionAdminResponse:
        metrics = await self._analytics.get_admin_dashboard(tenant_id=tenant_id)
        return InterventionAdminResponse(**metrics)

    async def export_csv(self, *, tenant_id: UUID) -> str:
        return await self._analytics.export_csv(tenant_id=tenant_id)

    async def get_successful_interventions(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        limit: int = 5,
    ) -> list[InterventionHistoryEntry]:
        rows = await self._repository.get_effectiveness_history(
            tenant_id=tenant_id,
            student_id=student_id,
            limit=limit,
        )
        successful = [row for row in rows if float(row.get("effectiveness_score") or 0) >= 80]
        return [
            InterventionHistoryEntry(
                intervention_id=row["intervention_id"],  # type: ignore[arg-type]
                intervention_type=str(row["intervention_type"]),
                concept_id=row.get("concept_id"),  # type: ignore[arg-type]
                concept=format_concept_name(str(row["concept_id"])) if row.get("concept_id") else None,
                status="completed",
                predicted_gain=float(row["predicted_gain"]),
                actual_gain=float(row["actual_gain"]),
                effectiveness_score=float(row["effectiveness_score"]),
                created_at=row["created_at"],  # type: ignore[arg-type]
                evaluated_at=row["evaluated_at"],  # type: ignore[arg-type]
            )
            for row in successful[:limit]
        ]

    async def get_failed_interventions(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        limit: int = 5,
    ) -> list[InterventionHistoryEntry]:
        rows = await self._repository.get_effectiveness_history(
            tenant_id=tenant_id,
            student_id=student_id,
            limit=limit,
        )
        failed = [row for row in rows if float(row.get("effectiveness_score") or 100) < 40]
        return [
            InterventionHistoryEntry(
                intervention_id=row["intervention_id"],  # type: ignore[arg-type]
                intervention_type=str(row["intervention_type"]),
                concept_id=row.get("concept_id"),  # type: ignore[arg-type]
                concept=format_concept_name(str(row["concept_id"])) if row.get("concept_id") else None,
                status="completed",
                predicted_gain=float(row["predicted_gain"]),
                actual_gain=float(row["actual_gain"]),
                effectiveness_score=float(row["effectiveness_score"]),
                created_at=row["created_at"],  # type: ignore[arg-type]
                evaluated_at=row["evaluated_at"],  # type: ignore[arg-type]
            )
            for row in failed[:limit]
        ]

    async def _build_optimizer_inputs(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        student_user_id: UUID,
        exam_id: str,
    ) -> dict[str, object]:
        dashboard = await self._twin_read_service.get_dashboard(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
        )
        recommendations_response = await self._recommendation_service.get_student_recommendations(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
            user_id=student_user_id,
            limit=8,
        )
        recommendations = recommendations_response.recommendations
        memory_context = await self._memory_service.load_student_context(
            tenant_id=tenant_id,
            user_id=student_user_id,
        )
        forecast = await self._forecasting_service.get_current_forecast(
            tenant_id=tenant_id,
            user_id=student_user_id,
            exam_id=exam_id,
        )
        forecast_risk = 50.0
        forecast_status = None
        if forecast is not None:
            forecast_status = forecast.forecast_status
            gap = max(0.0, forecast.target_readiness - forecast.projected_readiness)
            forecast_risk = min(100.0, gap * 2.0 + max(0.0, 100.0 - forecast.probability_of_success) * 0.5)
        elif dashboard.on_track is False:
            forecast_risk = 75.0

        memory_signal = min(100.0, len(memory_context.context_lines) * 12.0)
        if dashboard.historical_effectiveness is not None:
            memory_signal = max(memory_signal, float(dashboard.historical_effectiveness))

        concept_candidates: list[dict[str, float | str]] = []
        drivers = forecast.top_drivers if forecast else list(dashboard.top_negative_drivers)
        for index, recommendation in enumerate(recommendations):
            weakness = float(recommendation.impact_score)
            pyq = 65.0 if "high_pyq_frequency" in recommendation.reason_codes else 35.0
            failure = 55.0 if "weakness_recovery" in recommendation.reason_codes else 35.0
            driver_boost = 65.0 if recommendation.concept_id in drivers else 45.0
            concept_candidates.append(
                {
                    "concept_id": recommendation.concept_id,
                    "concept_name": format_concept_name(recommendation.concept_id),
                    "weakness": weakness,
                    "pyq_importance": pyq,
                    "historical_failure": failure,
                    "forecast_risk": driver_boost if forecast_risk >= 55 else forecast_risk,
                }
            )
            if index >= 7:
                break

        if not concept_candidates and drivers:
            for driver in drivers[:5]:
                concept_candidates.append(
                    {
                        "concept_id": driver,
                        "concept_name": format_concept_name(driver),
                        "weakness": 70.0,
                        "pyq_importance": 50.0,
                        "historical_failure": 40.0,
                        "forecast_risk": forecast_risk,
                    }
                )

        return {
            "concept_candidates": concept_candidates,
            "forecast_risk": forecast_risk,
            "memory_signal": memory_signal,
            "current_readiness": float(dashboard.readiness_score) if dashboard.readiness_score is not None else None,
            "forecast_status": forecast_status,
        }

    @staticmethod
    def _map_ranked(item) -> RecommendedInterventionItem:
        return RecommendedInterventionItem(
            intervention_type=item.intervention_type,
            concept_id=item.concept_id,
            concept=item.concept_name,
            predicted_gain=item.predicted_gain,
            priority_score=item.priority_score,
            impact_score=item.impact_score,
            confidence=item.confidence,
            reason=item.reason,
            forecast_improvement=item.forecast_improvement,
            score_breakdown=item.score_breakdown,
        )

    @staticmethod
    def _map_recommendation(row: dict[str, object]) -> RecommendedInterventionItem:
        concept_id = row.get("concept_id")
        return RecommendedInterventionItem(
            id=row.get("id"),  # type: ignore[arg-type]
            intervention_type=str(row["intervention_type"]),
            concept_id=str(concept_id) if concept_id else None,
            concept=format_concept_name(str(concept_id)) if concept_id else None,
            predicted_gain=float(row["predicted_gain"]),
            priority_score=float(row["impact_score"]),
            impact_score=float(row["impact_score"]),
            confidence=str(row["confidence"]),
            reason=str(row["recommendation_reason"]),
        )

    @staticmethod
    def _map_intervention(row: dict[str, object]) -> InterventionRecordResponse:
        concept_id = row.get("concept_id")
        return InterventionRecordResponse(
            id=row["id"],  # type: ignore[arg-type]
            mentor_id=row["mentor_id"],  # type: ignore[arg-type]
            student_id=row["student_id"],  # type: ignore[arg-type]
            exam_id=str(row["exam_id"]),
            intervention_type=str(row["intervention_type"]),
            concept_id=str(concept_id) if concept_id else None,
            concept=format_concept_name(str(concept_id)) if concept_id else None,
            reason=str(row["reason"]),
            predicted_gain=float(row["predicted_gain"]),
            priority_score=float(row["priority_score"]),
            status=str(row["status"]),
            created_at=row["created_at"],  # type: ignore[arg-type]
        )
