from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from prepos.domain.learning_graph.entities import LearningGraphReadinessSnapshot
from prepos.domain.revision_queue.entities import RevisionQueueItem
from prepos.domain.scoring.common import round_score
from prepos.domain.study_plan.adaptive_priority_v1 import compute_adaptive_priority_v1
from prepos.domain.study_plan.behavior_metrics_v1 import ConceptBehaviorStats, StudyBehaviorMetrics
from prepos.domain.study_plan.entities import DailyPlanItem, StudyPlan, WeeklyPlanItem
from prepos.domain.study_plan.plan_adjustment_explanations_v1 import explain_plan_adjustment_v1
from prepos.domain.study_plan.value_objects import ActivityType
from prepos.domain.twin.behavior_profile_types_v1 import LearningStyle
from prepos.domain.twin.entities import TwinRecommendation
from prepos.domain.twin.value_objects import RecommendationType

PLAN_GENERATOR_V1 = "plan_generator_v1"
DEFAULT_DAILY_MINUTES = 120
WEEKLY_DAY_MULTIPLIER = 7

_SESSION_MINUTES: dict[ActivityType, int] = {
    ActivityType.REVISION: 20,
    ActivityType.WEAKNESS_RECOVERY: 30,
    ActivityType.HIGH_IMPORTANCE_STUDY: 40,
    ActivityType.READINESS_BOOST: 20,
}

_TARGET_SESSIONS: dict[RecommendationType, int] = {
    RecommendationType.REVISION_DUE: 3,
    RecommendationType.WEAKNESS_RECOVERY: 2,
    RecommendationType.HIGH_IMPORTANCE_GAP: 2,
    RecommendationType.READINESS_BOOST: 1,
}


@dataclass(frozen=True, slots=True)
class PlanGeneratorInputs:
    tenant_id: UUID
    student_id: UUID
    exam_id: str
    recommendations: tuple[TwinRecommendation, ...]
    revision_queue: tuple[RevisionQueueItem, ...]
    readiness_snapshot: LearningGraphReadinessSnapshot | None
    generated_at: datetime
    behavior_metrics: StudyBehaviorMetrics | None = None
    learning_style: LearningStyle | None = None
    default_daily_minutes: int = DEFAULT_DAILY_MINUTES


@dataclass(frozen=True, slots=True)
class _PlanCandidate:
    concept_id: str
    recommendation_type: RecommendationType
    activity_type: ActivityType
    priority_score: Decimal
    adaptive_priority: Decimal
    readiness_gain: Decimal
    adjustment_explanation: str


def recommendation_type_to_activity(recommendation_type: RecommendationType) -> ActivityType:
    if recommendation_type == RecommendationType.REVISION_DUE:
        return ActivityType.REVISION
    if recommendation_type == RecommendationType.WEAKNESS_RECOVERY:
        return ActivityType.WEAKNESS_RECOVERY
    if recommendation_type == RecommendationType.HIGH_IMPORTANCE_GAP:
        return ActivityType.HIGH_IMPORTANCE_STUDY
    return ActivityType.READINESS_BOOST


def session_minutes_for_type(
    recommendation_type: RecommendationType,
    *,
    learning_style: LearningStyle | None = None,
) -> int:
    activity = recommendation_type_to_activity(recommendation_type)
    return session_minutes_for_activity(activity, learning_style=learning_style)


def session_minutes_for_activity(
    activity_type: ActivityType,
    *,
    learning_style: LearningStyle | None = None,
) -> int:
    if learning_style == LearningStyle.SHORT_BURST_LEARNER:
        return 18
    if learning_style == LearningStyle.DEEP_FOCUS_LEARNER:
        if activity_type == ActivityType.HIGH_IMPORTANCE_STUDY:
            return 55
        if activity_type == ActivityType.WEAKNESS_RECOVERY:
            return 50
        return 45
    minutes = _SESSION_MINUTES[activity_type]
    if learning_style == LearningStyle.RECOVERY_DRIVEN and activity_type == ActivityType.WEAKNESS_RECOVERY:
        return int(Decimal(minutes) * Decimal("1.30"))
    return minutes


def _behavior_for_concept(
    inputs: PlanGeneratorInputs,
    concept_id: str,
) -> ConceptBehaviorStats:
    if inputs.behavior_metrics is None:
        return ConceptBehaviorStats(
            completion_rate=Decimal("0"),
            skip_rate=Decimal("0"),
            average_minutes_variance=Decimal("0"),
        )
    return inputs.behavior_metrics.by_concept.get(
        concept_id,
        ConceptBehaviorStats(
            completion_rate=Decimal("0"),
            skip_rate=Decimal("0"),
            average_minutes_variance=Decimal("0"),
        ),
    )


def _build_candidates(inputs: PlanGeneratorInputs) -> list[_PlanCandidate]:
    candidates: dict[str, _PlanCandidate] = {}

    for recommendation in inputs.recommendations:
        try:
            recommendation_type = RecommendationType(recommendation.recommendation_type)
        except ValueError:
            continue
        behavior = _behavior_for_concept(inputs, recommendation.concept_id)
        adaptive_priority = compute_adaptive_priority_v1(
            priority_score=recommendation.recommendation_score,
            completion_rate=behavior.completion_rate,
            skip_rate=behavior.skip_rate,
        )
        candidates[recommendation.concept_id] = _PlanCandidate(
            concept_id=recommendation.concept_id,
            recommendation_type=recommendation_type,
            activity_type=recommendation_type_to_activity(recommendation_type),
            priority_score=recommendation.recommendation_score,
            adaptive_priority=adaptive_priority,
            readiness_gain=recommendation.readiness_gain,
            adjustment_explanation=explain_plan_adjustment_v1(
                priority_score=recommendation.recommendation_score,
                adaptive_priority=adaptive_priority,
                readiness_gain=recommendation.readiness_gain,
                behavior=behavior,
            ),
        )

    for queue_item in inputs.revision_queue:
        if queue_item.concept_id in candidates:
            continue
        behavior = _behavior_for_concept(inputs, queue_item.concept_id)
        adaptive_priority = compute_adaptive_priority_v1(
            priority_score=queue_item.priority_score,
            completion_rate=behavior.completion_rate,
            skip_rate=behavior.skip_rate,
        )
        readiness_gain = round_score(queue_item.weakness_score or Decimal("0"))
        candidates[queue_item.concept_id] = _PlanCandidate(
            concept_id=queue_item.concept_id,
            recommendation_type=RecommendationType.REVISION_DUE,
            activity_type=ActivityType.REVISION,
            priority_score=queue_item.priority_score,
            adaptive_priority=adaptive_priority,
            readiness_gain=readiness_gain,
            adjustment_explanation=explain_plan_adjustment_v1(
                priority_score=queue_item.priority_score,
                adaptive_priority=adaptive_priority,
                readiness_gain=readiness_gain,
                behavior=behavior,
            ),
        )

    return sorted(
        candidates.values(),
        key=lambda item: (-item.adaptive_priority, -item.readiness_gain, item.concept_id),
    )


def generate_daily_plan(
    inputs: PlanGeneratorInputs,
    *,
    candidates: list[_PlanCandidate] | None = None,
) -> tuple[DailyPlanItem, ...]:
    remaining_minutes = inputs.default_daily_minutes
    daily_items: list[DailyPlanItem] = []
    ordered = candidates if candidates is not None else _build_candidates(inputs)

    for candidate in ordered:
        session_minutes = session_minutes_for_activity(
            candidate.activity_type,
            learning_style=inputs.learning_style,
        )
        if remaining_minutes < session_minutes:
            continue
        daily_items.append(
            DailyPlanItem(
                concept_id=candidate.concept_id,
                activity_type=candidate.activity_type,
                estimated_minutes=session_minutes,
                priority_score=candidate.priority_score,
                adaptive_priority=candidate.adaptive_priority,
                readiness_gain=candidate.readiness_gain,
                adjustment_explanation=candidate.adjustment_explanation,
            )
        )
        remaining_minutes -= session_minutes

    return tuple(daily_items)


def generate_weekly_plan(
    inputs: PlanGeneratorInputs,
    *,
    candidates: list[_PlanCandidate] | None = None,
) -> tuple[WeeklyPlanItem, ...]:
    ordered = candidates if candidates is not None else _build_candidates(inputs)
    weekly_items: list[WeeklyPlanItem] = []

    for candidate in ordered:
        target_sessions = _TARGET_SESSIONS[candidate.recommendation_type]
        session_minutes = session_minutes_for_activity(
            candidate.activity_type,
            learning_style=inputs.learning_style,
        )
        weekly_items.append(
            WeeklyPlanItem(
                concept_id=candidate.concept_id,
                target_sessions=target_sessions,
                estimated_minutes=target_sessions * session_minutes,
                readiness_gain=round_score(candidate.readiness_gain * Decimal(target_sessions)),
            )
        )

    return tuple(weekly_items)


def generate_study_plan_v1(inputs: PlanGeneratorInputs) -> StudyPlan:
    candidates = _build_candidates(inputs)
    daily_plan = generate_daily_plan(inputs, candidates=candidates)
    weekly_plan = generate_weekly_plan(inputs, candidates=candidates)
    return StudyPlan(
        tenant_id=inputs.tenant_id,
        student_id=inputs.student_id,
        exam_id=inputs.exam_id,
        generated_at=inputs.generated_at,
        daily_plan=daily_plan,
        weekly_plan=weekly_plan,
    )
