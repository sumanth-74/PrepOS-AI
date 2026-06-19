from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from prepos.domain.scoring.common import clamp, round_score
from prepos.domain.study_plan.value_objects import ActivityType
from prepos.domain.twin.behavior_profile_types_v1 import LearningStyle, RiskProfile
from prepos.domain.twin.behavior_profile_v1 import BehaviorProfile
from prepos.domain.twin.intervention_history_entities import StudentInterventionHistoryEntry
from prepos.domain.twin.personalization_v1 import PERSONALIZATION_V1

PERSONALIZED_SCORING_V1 = "personalized_scoring_v1"

_HIGH_RISK_ADJUSTMENT = Decimal("15")
_MEDIUM_RISK_ADJUSTMENT = Decimal("5")

_STYLE_MULTIPLIERS: dict[LearningStyle, dict[ActivityType, Decimal]] = {
    LearningStyle.SHORT_BURST_LEARNER: {
        ActivityType.REVISION: Decimal("1.20"),
        ActivityType.WEAKNESS_RECOVERY: Decimal("1.10"),
        ActivityType.HIGH_IMPORTANCE_STUDY: Decimal("0.95"),
        ActivityType.READINESS_BOOST: Decimal("1.00"),
    },
    LearningStyle.DEEP_FOCUS_LEARNER: {
        ActivityType.HIGH_IMPORTANCE_STUDY: Decimal("1.20"),
        ActivityType.READINESS_BOOST: Decimal("1.10"),
        ActivityType.REVISION: Decimal("1.00"),
        ActivityType.WEAKNESS_RECOVERY: Decimal("1.00"),
    },
    LearningStyle.CONSISTENT_LEARNER: {
        ActivityType.REVISION: Decimal("1.05"),
        ActivityType.WEAKNESS_RECOVERY: Decimal("1.05"),
        ActivityType.HIGH_IMPORTANCE_STUDY: Decimal("1.05"),
        ActivityType.READINESS_BOOST: Decimal("1.05"),
    },
    LearningStyle.RECOVERY_DRIVEN: {
        ActivityType.WEAKNESS_RECOVERY: Decimal("1.30"),
        ActivityType.REVISION: Decimal("1.00"),
        ActivityType.HIGH_IMPORTANCE_STUDY: Decimal("1.00"),
        ActivityType.READINESS_BOOST: Decimal("1.00"),
    },
    LearningStyle.BALANCED: {
        ActivityType.REVISION: Decimal("1.00"),
        ActivityType.WEAKNESS_RECOVERY: Decimal("1.00"),
        ActivityType.HIGH_IMPORTANCE_STUDY: Decimal("1.00"),
        ActivityType.READINESS_BOOST: Decimal("1.00"),
    },
}

_INTERVENTION_TO_ACTIVITY: dict[str, ActivityType] = {
    "REVISION_SPRINT": ActivityType.REVISION,
    "WEAKNESS_REMEDIATION": ActivityType.WEAKNESS_RECOVERY,
    "COVERAGE_RECOVERY": ActivityType.HIGH_IMPORTANCE_STUDY,
    "CAPACITY_INCREASE": ActivityType.READINESS_BOOST,
    "CAPACITY_REDUCTION": ActivityType.READINESS_BOOST,
    "MAINTAIN_COURSE": ActivityType.READINESS_BOOST,
    "MOCK_TEST": ActivityType.HIGH_IMPORTANCE_STUDY,
}


@dataclass(frozen=True, slots=True)
class PersonalizationContext:
    learning_style: LearningStyle
    risk_profile: RiskProfile
    effectiveness_by_activity: dict[str, Decimal]


@dataclass(frozen=True, slots=True)
class PersonalizedScore:
    base_score: Decimal
    personalization_multiplier: Decimal
    personalized_score: Decimal
    explanation: str


@dataclass(frozen=True, slots=True)
class PersonalizationSummary:
    learning_style: LearningStyle
    risk_profile: RiskProfile
    top_multiplier: Decimal
    best_activity_type: ActivityType
    historical_effectiveness: Decimal


def map_intervention_type_to_activity(intervention_type: str) -> ActivityType:
    return _INTERVENTION_TO_ACTIVITY.get(intervention_type, ActivityType.READINESS_BOOST)


def build_effectiveness_by_activity(
    outcomes: tuple[StudentInterventionHistoryEntry, ...],
) -> dict[str, Decimal]:
    grouped: dict[str, list[Decimal]] = {}
    for outcome in outcomes:
        activity = map_intervention_type_to_activity(outcome.intervention_type)
        grouped.setdefault(activity.value, []).append(outcome.effectiveness_score)
    return {
        activity: round_score(sum(scores, start=Decimal("0")) / Decimal(len(scores)))
        for activity, scores in grouped.items()
        if scores
    }


def build_personalization_context(
    *,
    profile: BehaviorProfile,
    effectiveness_by_activity: dict[str, Decimal],
) -> PersonalizationContext:
    return PersonalizationContext(
        learning_style=profile.learning_style,
        risk_profile=profile.risk_profile,
        effectiveness_by_activity=effectiveness_by_activity,
    )


def learning_style_multiplier(
    *,
    learning_style: LearningStyle,
    activity_type: ActivityType,
) -> Decimal:
    multipliers = _STYLE_MULTIPLIERS.get(learning_style, _STYLE_MULTIPLIERS[LearningStyle.BALANCED])
    return multipliers.get(activity_type, Decimal("1.00"))


def historical_effectiveness_multiplier(*, historical_effectiveness: Decimal) -> Decimal:
    return Decimal("1") + historical_effectiveness / Decimal("200")


def risk_score_adjustment(*, risk_profile: RiskProfile) -> Decimal:
    if risk_profile == RiskProfile.HIGH_RISK:
        return _HIGH_RISK_ADJUSTMENT
    if risk_profile == RiskProfile.MEDIUM_RISK:
        return _MEDIUM_RISK_ADJUSTMENT
    return Decimal("0")


def compute_personalization_multiplier(
    *,
    learning_style: LearningStyle,
    activity_type: ActivityType,
    historical_effectiveness: Decimal,
) -> Decimal:
    style_multiplier = learning_style_multiplier(
        learning_style=learning_style,
        activity_type=activity_type,
    )
    effectiveness_multiplier = historical_effectiveness_multiplier(
        historical_effectiveness=historical_effectiveness,
    )
    return round_score(style_multiplier * effectiveness_multiplier, places=4)


def compute_personalized_score_v1(
    *,
    base_score: Decimal,
    learning_style: LearningStyle,
    risk_profile: RiskProfile,
    activity_type: ActivityType,
    historical_effectiveness: Decimal,
) -> PersonalizedScore:
    multiplier = compute_personalization_multiplier(
        learning_style=learning_style,
        activity_type=activity_type,
        historical_effectiveness=historical_effectiveness,
    )
    adjusted = base_score * multiplier + risk_score_adjustment(risk_profile=risk_profile)
    personalized_score = round_score(clamp(adjusted, Decimal("0"), Decimal("100")))
    return PersonalizedScore(
        base_score=base_score,
        personalization_multiplier=multiplier,
        personalized_score=personalized_score,
        explanation="",
    )


def select_best_activity_type(
    *,
    learning_style: LearningStyle,
    effectiveness_by_activity: dict[str, Decimal],
) -> tuple[ActivityType, Decimal, Decimal]:
    best_activity = ActivityType.WEAKNESS_RECOVERY
    best_effectiveness = Decimal("0")
    best_multiplier = Decimal("1.00")
    for activity in ActivityType:
        effectiveness = effectiveness_by_activity.get(activity.value, Decimal("0"))
        multiplier = compute_personalization_multiplier(
            learning_style=learning_style,
            activity_type=activity,
            historical_effectiveness=effectiveness,
        )
        if effectiveness > best_effectiveness or (
            effectiveness == best_effectiveness and multiplier > best_multiplier
        ):
            best_activity = activity
            best_effectiveness = effectiveness
            best_multiplier = multiplier
    return best_activity, best_effectiveness, best_multiplier


def build_personalization_summary(
    *,
    profile: BehaviorProfile,
    effectiveness_by_activity: dict[str, Decimal],
) -> PersonalizationSummary:
    best_activity, historical_effectiveness, top_multiplier = select_best_activity_type(
        learning_style=profile.learning_style,
        effectiveness_by_activity=effectiveness_by_activity,
    )
    return PersonalizationSummary(
        learning_style=profile.learning_style,
        risk_profile=profile.risk_profile,
        top_multiplier=top_multiplier,
        best_activity_type=best_activity,
        historical_effectiveness=historical_effectiveness,
    )


def build_personalization_payload_section(
    *,
    summary: PersonalizationSummary,
    explanation: str = "",
) -> dict[str, object]:
    return {
        "version": PERSONALIZATION_V1,
        "learning_style": summary.learning_style.value,
        "risk_profile": summary.risk_profile.value,
        "top_multiplier": float(summary.top_multiplier),
        "best_activity_type": summary.best_activity_type.value,
        "historical_effectiveness": float(summary.historical_effectiveness),
        "explanation": explanation,
    }
