from __future__ import annotations

from decimal import Decimal

from prepos.domain.scoring.decision_impact_v1 import DecisionImpactInputs, compute_decision_impact_v1
from prepos.domain.twin.decision_types_v1 import TwinDecisionType


def test_revise_now_impact_uses_retention_model() -> None:
    impact = compute_decision_impact_v1(
        decision_type=TwinDecisionType.REVISE_NOW.value,
        inputs=DecisionImpactInputs(
            due_revision_count=2,
            high_risk_concept_count=0,
            coverage_subscore=Decimal("70"),
            retention_subscore=Decimal("55"),
            total_estimated_gain=Decimal("5"),
            required_gain=Decimal("10"),
            goal_probability=Decimal("70"),
        ),
    )
    assert impact.expected_readiness_gain == Decimal("6.75")
    assert impact.expected_score_gain == Decimal("4.73")


def test_focus_weakness_impact_scales_with_high_risk_count() -> None:
    impact = compute_decision_impact_v1(
        decision_type=TwinDecisionType.FOCUS_WEAKNESS.value,
        inputs=DecisionImpactInputs(
            due_revision_count=0,
            high_risk_concept_count=3,
            coverage_subscore=Decimal("70"),
            retention_subscore=Decimal("70"),
            total_estimated_gain=Decimal("0"),
            required_gain=Decimal("0"),
            goal_probability=Decimal("70"),
        ),
    )
    assert impact.expected_readiness_gain == Decimal("4.50")
    assert impact.expected_score_gain == Decimal("3.15")


def test_increase_daily_capacity_impact_uses_required_gain() -> None:
    impact = compute_decision_impact_v1(
        decision_type=TwinDecisionType.INCREASE_DAILY_CAPACITY.value,
        inputs=DecisionImpactInputs(
            due_revision_count=0,
            high_risk_concept_count=0,
            coverage_subscore=Decimal("70"),
            retention_subscore=Decimal("70"),
            total_estimated_gain=Decimal("8"),
            required_gain=Decimal("12"),
            goal_probability=Decimal("55"),
        ),
    )
    assert impact.expected_readiness_gain == Decimal("9.80")
    assert impact.expected_score_gain == Decimal("6.86")
