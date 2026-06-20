from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from prepos.application.goal.dto import GoalResponse
from prepos.application.learning_graph.dto import WeaknessItemResponse
from prepos.application.pyq.ports import PyqStatisticRecord
from prepos.application.recommendations.impact_scoring import (
    ImpactInputs,
    compute_impact,
    estimate_readiness_gain,
    forecast_gain_score,
    human_reasons,
    normalize_score,
    pyq_frequency_score,
    current_affairs_score_for_concept,
    recommendation_confidence,
)
from prepos.application.recommendations.recommendation_models import ConceptRecommendation
from prepos.application.study_plan.dto import DailyPlanItemResponse
from prepos.application.twin.dto import TwinRecommendationResponse
from prepos.application.twin.twin_dto import TwinDashboardResponse


@dataclass(frozen=True, slots=True)
class RecommendationContext:
    tenant_id: UUID
    student_id: UUID
    exam_id: str
    dashboard: TwinDashboardResponse
    weaknesses: list[WeaknessItemResponse]
    goal: GoalResponse | None
    study_plan_items: list[DailyPlanItemResponse]
    twin_recommendations: list[TwinRecommendationResponse]
    pyq_statistics: list[PyqStatisticRecord]


def format_concept_name(concept_id: str) -> str:
    token = concept_id.split(".")[-1] if "." in concept_id else concept_id
    return token.replace("_", " ").strip().title()


class LearningRecommendationEngine:
    def generate(
        self,
        *,
        context: RecommendationContext,
        limit: int = 5,
    ) -> list[ConceptRecommendation]:
        pyq_by_concept = {stat.concept_id: stat for stat in context.pyq_statistics}
        twin_by_concept = {item.concept_id: item for item in context.twin_recommendations}
        plan_by_concept = {item.concept_id: item for item in context.study_plan_items}

        candidate_ids: list[str] = []
        for weakness in context.weaknesses:
            if weakness.concept_id not in candidate_ids:
                candidate_ids.append(weakness.concept_id)
        for item in context.twin_recommendations:
            if item.concept_id not in candidate_ids:
                candidate_ids.append(item.concept_id)
        for item in context.study_plan_items:
            if item.concept_id not in candidate_ids:
                candidate_ids.append(item.concept_id)
        for stat in sorted(context.pyq_statistics, key=lambda row: row.frequency_score, reverse=True)[:10]:
            if stat.concept_id not in candidate_ids:
                candidate_ids.append(stat.concept_id)

        recommendations: list[ConceptRecommendation] = []
        for concept_id in candidate_ids:
            weakness = next((item for item in context.weaknesses if item.concept_id == concept_id), None)
            pyq = pyq_by_concept.get(concept_id)
            twin = twin_by_concept.get(concept_id)
            plan = plan_by_concept.get(concept_id)

            weakness_score = normalize_score(weakness.weakness_score if weakness else None)
            pyq_freq = pyq_frequency_score(
                frequency_score=pyq.frequency_score if pyq else 0.0,
                pyq_count=pyq.pyq_count if pyq else 0,
            )
            readiness_gain = twin.readiness_gain if twin else (plan.readiness_gain if plan else Decimal("0"))
            importance = weakness.importance_score if weakness else (twin.importance_score if twin else Decimal("0"))
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
                current_affairs_label=(
                    "Linked to current affairs themes"
                    if "current_affairs_relevant" in breakdown.reason_codes
                    else None
                ),
            )
            estimated_gain = estimate_readiness_gain(
                impact_score=breakdown.impact_score,
                weakness_score=breakdown.weakness_score,
            )
            confidence = recommendation_confidence(
                impact_score=breakdown.impact_score,
                reason_count=len(breakdown.reason_codes),
            )
            recommendations.append(
                ConceptRecommendation(
                    concept_id=concept_id,
                    concept_name=format_concept_name(concept_id),
                    impact_score=breakdown.impact_score,
                    reason_codes=list(breakdown.reason_codes),
                    reasons=reasons,
                    estimated_readiness_gain=estimated_gain,
                    confidence=confidence,  # type: ignore[arg-type]
                )
            )

        recommendations.sort(key=lambda item: (item.impact_score, item.estimated_readiness_gain), reverse=True)
        return recommendations[:limit]

    def explain(
        self,
        *,
        context: RecommendationContext,
        concept_id: str,
    ) -> ConceptRecommendation | None:
        matches = self.generate(context=context, limit=50)
        for item in matches:
            if item.concept_id == concept_id:
                return item
        return None
