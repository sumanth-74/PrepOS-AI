from __future__ import annotations

from decimal import Decimal

from prepos.domain.mentor.mentor_effectiveness_learning_v1 import (
    ActionEffectivenessSample,
    apply_optimized_priority_v1,
    compute_action_effectiveness_v1,
    compute_mentor_effectiveness_learning_v1,
    rank_action_effectiveness_v1,
)
from prepos.domain.mentor.mentor_types_v1 import CaseResolutionReason, MentorActionType


def _sample(
    action_type: MentorActionType,
    *,
    reason: CaseResolutionReason = CaseResolutionReason.RISK_REDUCED,
    readiness_delta: Decimal = Decimal("10"),
    predicted_score_delta: Decimal = Decimal("8"),
) -> ActionEffectivenessSample:
    return ActionEffectivenessSample(
        action_type=action_type,
        resolution_reason=reason,
        readiness_delta=readiness_delta,
        predicted_score_delta=predicted_score_delta,
    )


def test_compute_action_effectiveness_uses_weighted_formula() -> None:
    samples = (
        _sample(MentorActionType.CONTACT_STUDENT),
        _sample(MentorActionType.CONTACT_STUDENT, reason=CaseResolutionReason.FALSE_POSITIVE),
    )
    result = compute_action_effectiveness_v1(
        action_type=MentorActionType.CONTACT_STUDENT,
        samples=samples,
    )
    assert result is not None
    assert result.sample_size == 2
    assert result.success_rate == Decimal("50.00")
    readiness_normalized = Decimal("10") / Decimal("20") * Decimal("100")
    predicted_normalized = Decimal("8") / Decimal("20") * Decimal("100")
    expected = (
        Decimal("50.00") * Decimal("0.40")
        + readiness_normalized * Decimal("0.30")
        + predicted_normalized * Decimal("0.30")
    ).quantize(Decimal("0.01"))
    assert result.effectiveness_score == expected


def test_rank_action_effectiveness_orders_by_score_sample_size_and_type() -> None:
    contact = compute_action_effectiveness_v1(
        action_type=MentorActionType.CONTACT_STUDENT,
        samples=(
            _sample(MentorActionType.CONTACT_STUDENT),
            _sample(MentorActionType.CONTACT_STUDENT),
        ),
    )
    sprint = compute_action_effectiveness_v1(
        action_type=MentorActionType.ASSIGN_REVISION_SPRINT,
        samples=(_sample(MentorActionType.ASSIGN_REVISION_SPRINT),),
    )
    review = compute_action_effectiveness_v1(
        action_type=MentorActionType.SCHEDULE_REVIEW,
        samples=(_sample(MentorActionType.SCHEDULE_REVIEW),),
    )
    assert contact is not None
    assert sprint is not None
    assert review is not None

    ranked = rank_action_effectiveness_v1((review, sprint, contact))
    assert ranked[0].action_type == MentorActionType.CONTACT_STUDENT
    assert ranked[1].action_type in {
        MentorActionType.ASSIGN_REVISION_SPRINT,
        MentorActionType.SCHEDULE_REVIEW,
    }


def test_compute_learning_summary_returns_weighted_average() -> None:
    samples = (
        _sample(MentorActionType.CONTACT_STUDENT),
        _sample(MentorActionType.CONTACT_STUDENT),
        _sample(MentorActionType.ASSIGN_REVISION_SPRINT),
    )
    result = compute_mentor_effectiveness_learning_v1(samples)
    assert result.best_action == MentorActionType.CONTACT_STUDENT
    assert result.best_action_effectiveness == result.action_effectiveness[0].effectiveness_score
    assert result.average_action_effectiveness > Decimal("0")


def test_apply_optimized_priority_scales_and_clamps() -> None:
    optimized = apply_optimized_priority_v1(
        base_priority=Decimal("50"),
        effectiveness_score=Decimal("84.20"),
    )
    assert optimized == Decimal("92.10")

    clamped = apply_optimized_priority_v1(
        base_priority=Decimal("90"),
        effectiveness_score=Decimal("100"),
    )
    assert clamped == Decimal("100.00")
