from __future__ import annotations

from decimal import Decimal

from prepos.domain.twin.intervention_explanations_v1 import (
    describe_intervention_v1,
    title_for_intervention_v1,
)
from prepos.domain.twin.intervention_types_v1 import InterventionUrgency, TwinInterventionType


def test_revision_sprint_title_includes_due_count() -> None:
    title = title_for_intervention_v1(
        intervention_type=TwinInterventionType.REVISION_SPRINT,
        urgency=InterventionUrgency.HIGH,
        due_revision_count=4,
    )
    assert title == "Complete 4 overdue revision sprint"


def test_capacity_increase_title_reflects_critical_urgency() -> None:
    title = title_for_intervention_v1(
        intervention_type=TwinInterventionType.CAPACITY_INCREASE,
        urgency=InterventionUrgency.CRITICAL,
        due_revision_count=0,
    )
    assert title == "Urgent: increase study capacity"


def test_weakness_remediation_description_is_deterministic() -> None:
    description = describe_intervention_v1(
        intervention_type=TwinInterventionType.WEAKNESS_REMEDIATION,
        urgency=InterventionUrgency.MEDIUM,
        expected_readiness_gain=Decimal("4.5"),
        daily_plan_count=3,
    )
    assert "4.5 readiness points" in description
