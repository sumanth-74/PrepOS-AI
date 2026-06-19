from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from prepos.domain.learning_graph.entities import ConceptProgressNode, LearningGraphReadinessSnapshot
from prepos.domain.learning_graph.policies import NodeStatus
from prepos.domain.scoring.common import clamp, round_score
from prepos.domain.scoring.readiness_drivers_v1 import ReadinessDriversV1
from prepos.domain.scoring.readiness_impact_v1 import compute_readiness_impact_v1
from prepos.domain.scoring.readiness_v1_1 import ReadinessResultV1_1
from prepos.domain.scoring.retention_v1 import RetentionInputs, compute_retention_v1
from prepos.domain.study_plan.plan_generator_v1 import recommendation_type_to_activity
from prepos.domain.twin.entities import TwinRecommendation
from prepos.domain.twin.personalized_scoring_v1 import PersonalizationContext, compute_personalized_score_v1
from prepos.domain.twin.value_objects import RecommendationType

TWIN_RECOMMENDATIONS_V1 = "twin_recommendations_v1"

_W_IMPORTANCE = Decimal("0.40")
_W_WEAKNESS = Decimal("0.30")
_W_RETENTION_RISK = Decimal("0.20")
_W_REVISION_DUE = Decimal("0.10")

_WEAKNESS_RECOVERY_THRESHOLD = Decimal("70")
_HIGH_IMPORTANCE_THRESHOLD = Decimal("80")
_LOW_MASTERY_THRESHOLD = Decimal("50")
_LOW_CONFIDENCE_THRESHOLD = Decimal("70")
MIN_RECOMMENDATION_SCORE = Decimal("10.00")


@dataclass(frozen=True, slots=True)
class TwinRecommendationInputs:
    nodes: tuple[ConceptProgressNode, ...]
    weakness_by_concept: dict[str, Decimal]
    due_concept_ids: frozenset[str]
    readiness_snapshot: LearningGraphReadinessSnapshot
    readiness_result: ReadinessResultV1_1 | None
    readiness_drivers: ReadinessDriversV1 | None
    current_time: datetime
    personalization: PersonalizationContext | None = None


def compute_retention_risk(retention_score: Decimal | None) -> Decimal:
    if retention_score is None:
        return Decimal("100")
    return clamp(Decimal("100") - retention_score, Decimal("0"), Decimal("100"))


def compute_revision_due_bonus(*, is_due: bool) -> Decimal:
    return Decimal("100") if is_due else Decimal("0")


def compute_recommendation_score(
    *,
    importance_score: Decimal,
    weakness_score: Decimal,
    retention_score: Decimal | None,
    is_due: bool,
) -> Decimal:
    retention_risk = compute_retention_risk(retention_score)
    revision_due_bonus = compute_revision_due_bonus(is_due=is_due)
    raw = (
        _W_IMPORTANCE * importance_score
        + _W_WEAKNESS * weakness_score
        + _W_RETENTION_RISK * retention_risk
        + _W_REVISION_DUE * revision_due_bonus
    )
    return round_score(clamp(raw, Decimal("0"), Decimal("100")))


def classify_recommendation_type(
    *,
    is_due: bool,
    weakness_score: Decimal,
    importance_score: Decimal,
    mastery_score: Decimal,
) -> RecommendationType:
    if is_due:
        return RecommendationType.REVISION_DUE
    if weakness_score >= _WEAKNESS_RECOVERY_THRESHOLD:
        return RecommendationType.WEAKNESS_RECOVERY
    if importance_score >= _HIGH_IMPORTANCE_THRESHOLD and mastery_score <= _LOW_MASTERY_THRESHOLD:
        return RecommendationType.HIGH_IMPORTANCE_GAP
    return RecommendationType.READINESS_BOOST


def _format_gain(readiness_gain: Decimal) -> str:
    return f"{readiness_gain:.2f}".rstrip("0").rstrip(".")


def explain_recommendation(
    recommendation_type: RecommendationType,
    *,
    readiness_gain: Decimal,
    readiness_result: ReadinessResultV1_1 | None = None,
    readiness_drivers: ReadinessDriversV1 | None = None,
) -> str:
    """Deterministic recommendation copy including estimated readiness improvement."""
    del readiness_result, readiness_drivers
    gain_text = _format_gain(readiness_gain)

    if recommendation_type == RecommendationType.REVISION_DUE:
        return (
            f"This concept is overdue for revision and is estimated to improve "
            f"readiness by {gain_text} points."
        )
    if recommendation_type == RecommendationType.WEAKNESS_RECOVERY:
        return (
            f"This weak concept has high improvement potential and could improve "
            f"readiness by {gain_text} points."
        )
    if recommendation_type == RecommendationType.HIGH_IMPORTANCE_GAP:
        return "This important concept is underperforming and could significantly increase readiness."
    return "This concept offers incremental readiness improvement."


def _materialized_retention(
    node: ConceptProgressNode,
    *,
    current_time: datetime,
) -> Decimal | None:
    result = compute_retention_v1(
        RetentionInputs(
            mastery_score=node.mastery_score,
            retention_stability_s=node.retention_stability_s,
            retention_last_review_at=node.retention_last_review_at,
            retention_last_grade=node.retention_last_grade,
            current_time=current_time,
            node_state=node.node_state,
        )
    )
    return result.value


def _build_recommendation(
    node: ConceptProgressNode,
    *,
    weakness_score: Decimal,
    is_due: bool,
    readiness_result: ReadinessResultV1_1 | None,
    readiness_drivers: ReadinessDriversV1 | None,
    current_time: datetime,
) -> TwinRecommendation | None:
    retention_score = _materialized_retention(node, current_time=current_time)
    recommendation_type = classify_recommendation_type(
        is_due=is_due,
        weakness_score=weakness_score,
        importance_score=node.importance_score,
        mastery_score=node.mastery_score,
    )
    recommendation_score = compute_recommendation_score(
        importance_score=node.importance_score,
        weakness_score=weakness_score,
        retention_score=retention_score,
        is_due=is_due,
    )
    if recommendation_score < MIN_RECOMMENDATION_SCORE:
        return None

    impact = compute_readiness_impact_v1(
        importance_score=node.importance_score,
        weakness_score=weakness_score,
        retention_score=retention_score,
        recommendation_type=recommendation_type.value,
    )

    return TwinRecommendation(
        concept_id=node.concept_id,
        recommendation_type=recommendation_type.value,
        recommendation_score=recommendation_score,
        importance_score=node.importance_score,
        weakness_score=weakness_score,
        retention_score=retention_score,
        readiness_gain=impact.readiness_gain,
        explanation=explain_recommendation(
            recommendation_type,
            readiness_gain=impact.readiness_gain,
            readiness_result=readiness_result,
            readiness_drivers=readiness_drivers,
        ),
    )


def compute_recommendation_for_concept(
    node: ConceptProgressNode,
    *,
    weakness_score: Decimal | None,
    is_due: bool,
    readiness_result: ReadinessResultV1_1 | None,
    readiness_drivers: ReadinessDriversV1 | None,
    current_time: datetime,
) -> TwinRecommendation | None:
    """Compute a single concept recommendation; None means the row should be deleted."""
    if node.node_state == NodeStatus.UNRATED:
        return None
    if weakness_score is None:
        return None

    return _build_recommendation(
        node,
        weakness_score=weakness_score,
        is_due=is_due,
        readiness_result=readiness_result,
        readiness_drivers=readiness_drivers,
        current_time=current_time,
    )


def compute_twin_recommendations_v1(inputs: TwinRecommendationInputs) -> tuple[TwinRecommendation, ...]:
    """Deterministic ranked recommendations optimized for expected readiness improvement."""
    recommendations: list[TwinRecommendation] = []

    for node in inputs.nodes:
        if node.node_state == NodeStatus.UNRATED:
            continue
        weakness_score = inputs.weakness_by_concept.get(node.concept_id)
        if weakness_score is None:
            continue

        recommendation = _build_recommendation(
            node,
            weakness_score=weakness_score,
            is_due=node.concept_id in inputs.due_concept_ids,
            readiness_result=inputs.readiness_result,
            readiness_drivers=inputs.readiness_drivers,
            current_time=inputs.current_time,
        )
        if recommendation is not None:
            recommendations.append(recommendation)

    if inputs.personalization is not None:
        recommendations.sort(
            key=lambda item: _personalized_rank_key(item, inputs.personalization),
        )
    else:
        recommendations.sort(
            key=lambda item: (-item.readiness_gain, -item.recommendation_score, item.concept_id),
        )
    return tuple(recommendations)


def _personalized_rank_key(
    recommendation: TwinRecommendation,
    personalization: PersonalizationContext,
) -> tuple[Decimal, Decimal, Decimal, str]:
    recommendation_type = RecommendationType(recommendation.recommendation_type)
    activity_type = recommendation_type_to_activity(recommendation_type)
    historical_effectiveness = personalization.effectiveness_by_activity.get(
        activity_type.value,
        Decimal("0"),
    )
    personalized = compute_personalized_score_v1(
        base_score=recommendation.recommendation_score,
        learning_style=personalization.learning_style,
        risk_profile=personalization.risk_profile,
        activity_type=activity_type,
        historical_effectiveness=historical_effectiveness,
    )
    return (
        -personalized.personalized_score,
        -recommendation.readiness_gain,
        -recommendation.recommendation_score,
        recommendation.concept_id,
    )
