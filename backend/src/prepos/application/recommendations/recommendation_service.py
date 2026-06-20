from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

import structlog

from prepos.application.goal.service import GoalService
from prepos.application.learning_graph.read_services import LearningGraphReadService
from prepos.application.pyq.ports import PyqRepositoryPort
from prepos.application.recommendations.impact_scoring import (
    ImpactInputs,
    WEAKNESS_WEIGHT,
    PYQ_FREQUENCY_WEIGHT,
    FORECAST_GAIN_WEIGHT,
    CURRENT_AFFAIRS_WEIGHT,
    compute_impact,
    current_affairs_score_for_concept,
    estimate_readiness_gain,
    forecast_gain_score,
    human_reasons,
    normalize_score,
    pyq_frequency_score,
    recommendation_confidence,
)
from prepos.application.recommendations.intent_ranking import apply_intent_ranking
from prepos.application.recommendations.outcomes.effectiveness_calculator import build_score_breakdown
from prepos.application.recommendations.ports import RecommendationAnalyticsRepositoryPort
from prepos.application.recommendations.recommendation_engine import (
    LearningRecommendationEngine,
    RecommendationContext,
    format_concept_name,
)
from prepos.application.recommendations.recommendation_models import (
    ConceptRecommendation,
    RecommendationExplainResponse,
    RecommendationExplainScoreBreakdown,
    RecommendationsResponse,
)
from prepos.application.study_plan.service import StudyPlanService
from prepos.application.twin.services import TwinRecommendationService
from prepos.application.twin.twin_read_service import TwinReadService

logger = structlog.get_logger(__name__)


class LearningRecommendationService:
    def __init__(
        self,
        *,
        twin_read_service: TwinReadService,
        learning_graph_read_service: LearningGraphReadService,
        goal_service: GoalService,
        study_plan_service: StudyPlanService,
        twin_recommendation_service: TwinRecommendationService,
        pyq_repository: PyqRepositoryPort,
        analytics_repository: RecommendationAnalyticsRepositoryPort | None = None,
        engine: LearningRecommendationEngine | None = None,
    ) -> None:
        self._twin_read_service = twin_read_service
        self._learning_graph_read_service = learning_graph_read_service
        self._goal_service = goal_service
        self._study_plan_service = study_plan_service
        self._twin_recommendation_service = twin_recommendation_service
        self._pyq_repository = pyq_repository
        self._analytics_repository = analytics_repository
        self._engine = engine or LearningRecommendationEngine()

    async def get_student_recommendations(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str | None,
        user_id: UUID | None,
        limit: int = 5,
    ) -> RecommendationsResponse:
        context = await self._build_context(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
        )
        recommendations = self._engine.generate(context=context, limit=limit)
        await self._record_generated(
            tenant_id=tenant_id,
            user_id=user_id,
            student_id=student_id,
            recommendations=recommendations,
            context=context,
        )
        return RecommendationsResponse(
            recommendations=recommendations,
            generated_at=datetime.now(UTC).isoformat(),
        )

    async def get_recommendations_for_intent(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str | None,
        user_id: UUID | None,
        intent: str,
        limit: int = 5,
    ) -> list[ConceptRecommendation]:
        context = await self._build_context(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
        )
        generated = self._engine.generate(context=context, limit=max(limit, 20))
        ranked = apply_intent_ranking(intent, generated)
        recommendations = ranked[:limit]
        await self._record_generated(
            tenant_id=tenant_id,
            user_id=user_id,
            student_id=student_id,
            recommendations=recommendations,
            context=context,
        )
        return recommendations

    async def get_mentor_recommendations(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str | None,
        user_id: UUID | None,
        limit: int = 5,
    ) -> RecommendationsResponse:
        return await self.get_student_recommendations(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
            user_id=user_id,
            limit=limit,
        )

    async def explain_concept(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str | None,
        concept_id: str,
    ) -> RecommendationExplainResponse:
        context = await self._build_context(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
        )
        pyq = next((item for item in context.pyq_statistics if item.concept_id == concept_id), None)
        weakness = next((item for item in context.weaknesses if item.concept_id == concept_id), None)
        twin = next((item for item in context.twin_recommendations if item.concept_id == concept_id), None)
        plan = next((item for item in context.study_plan_items if item.concept_id == concept_id), None)

        weakness_score = normalize_score(weakness.weakness_score if weakness else None)
        pyq_freq = pyq_frequency_score(
            frequency_score=pyq.frequency_score if pyq else 0.0,
            pyq_count=pyq.pyq_count if pyq else 0,
        )
        readiness_gain = twin.readiness_gain if twin else (plan.readiness_gain if plan else 0)
        importance = weakness.importance_score if weakness else (twin.importance_score if twin else 0)
        forecast = forecast_gain_score(
            readiness_gain=readiness_gain,
            gap_to_goal=context.dashboard.gap_to_goal,
            importance_score=importance,
        )
        ca_score = current_affairs_score_for_concept(concept_id)
        breakdown = compute_impact(
            ImpactInputs(
                weakness_score=weakness_score,
                pyq_frequency_score=pyq_freq,
                forecast_gain_score=forecast,
                current_affairs_score=ca_score,
            )
        )
        reasons = human_reasons(
            reason_codes=breakdown.reason_codes,
            pyq_count=pyq.pyq_count if pyq else 0,
        )
        estimated_gain = estimate_readiness_gain(
            impact_score=breakdown.impact_score,
            weakness_score=breakdown.weakness_score,
        )
        confidence = recommendation_confidence(
            impact_score=breakdown.impact_score,
            reason_count=len(breakdown.reason_codes),
        )
        score_breakdown = build_score_breakdown(
            weakness_score=breakdown.weakness_score,
            pyq_frequency_score=breakdown.pyq_frequency_score,
            forecast_gain_score=breakdown.forecast_gain_score,
            current_affairs_score=breakdown.current_affairs_score,
            weakness_weight=WEAKNESS_WEIGHT,
            pyq_weight=PYQ_FREQUENCY_WEIGHT,
            forecast_weight=FORECAST_GAIN_WEIGHT,
            current_affairs_weight=CURRENT_AFFAIRS_WEIGHT,
        )
        return RecommendationExplainResponse(
            concept_id=concept_id,
            concept_name=format_concept_name(concept_id),
            impact_score=breakdown.impact_score,
            weakness_score=breakdown.weakness_score,
            pyq_frequency_score=breakdown.pyq_frequency_score,
            forecast_gain_score=breakdown.forecast_gain_score,
            current_affairs_score=breakdown.current_affairs_score,
            reason_codes=list(breakdown.reason_codes),
            reasons=reasons,
            estimated_readiness_gain=estimated_gain,
            confidence=confidence,  # type: ignore[arg-type]
            score_breakdown=RecommendationExplainScoreBreakdown(**score_breakdown),
        )

    async def _build_context(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str | None,
    ) -> RecommendationContext:
        resolved_exam_id = exam_id or "upsc_cse"
        dashboard = await self._twin_read_service.get_dashboard(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=resolved_exam_id,
        )
        weaknesses = await self._learning_graph_read_service.get_weaknesses(
            tenant_id=tenant_id,
            student_id=student_id,
            limit=12,
        )
        goal = await self._goal_service.get_goal(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=resolved_exam_id,
        )
        study_plan = await self._study_plan_service.get_study_plan(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=resolved_exam_id,
        )
        twin_recommendations = await self._twin_recommendation_service.list_recommendations(
            tenant_id=tenant_id,
            student_id=student_id,
            limit=12,
        )
        pyq_statistics = await self._pyq_repository.list_statistics(exam_id=resolved_exam_id, limit=100)
        return RecommendationContext(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=resolved_exam_id,
            dashboard=dashboard,
            weaknesses=weaknesses.weaknesses,
            goal=goal,
            study_plan_items=study_plan.daily_plan,
            twin_recommendations=twin_recommendations,
            pyq_statistics=pyq_statistics,
        )

    async def _record_generated(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID | None,
        student_id: UUID,
        recommendations: list[ConceptRecommendation],
        context: RecommendationContext,
    ) -> None:
        if self._analytics_repository is None:
            return
        now = datetime.now(UTC)
        weakness_by_concept = {item.concept_id: item for item in context.weaknesses}
        readiness_before = float(context.dashboard.readiness_score) if context.dashboard.readiness_score else None
        forecast_before = (
            float(context.dashboard.projected_readiness) if context.dashboard.projected_readiness else None
        )
        for item in recommendations:
            weakness = weakness_by_concept.get(item.concept_id)
            weakness_before = float(weakness.weakness_score) if weakness else None
            await self._analytics_repository.record_event(
                tenant_id=tenant_id,
                user_id=user_id,
                student_id=student_id,
                event_type="recommendation_shown",
                concept_id=item.concept_id,
                impact_score=item.impact_score,
                estimated_gain=item.estimated_readiness_gain,
                readiness_gain_after=None,
                metadata_json={
                    "reason_codes": item.reason_codes,
                    "readiness_before": readiness_before,
                    "forecast_before": forecast_before,
                    "weakness_before": weakness_before,
                    "predicted_gain": item.estimated_readiness_gain,
                    "exam_id": context.exam_id,
                },
                created_at=now,
            )
            logger.info(
                "recommendation_generated",
                tenant_id=str(tenant_id),
                user_id=str(user_id) if user_id else None,
                concept_id=item.concept_id,
                impact_score=item.impact_score,
                estimated_gain=item.estimated_readiness_gain,
            )
