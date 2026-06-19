from __future__ import annotations

from decimal import Decimal

from prepos.domain.twin.intervention_outcome_explanations_v1 import explain_intervention_outcome_v1
from prepos.domain.twin.intervention_outcome_types_v1 import InterventionOutcomeStatus
from prepos.domain.twin.intervention_types_v1 import TwinInterventionType


def test_positive_outcome_explanation() -> None:
    explanation = explain_intervention_outcome_v1(
        intervention_type=TwinInterventionType.REVISION_SPRINT,
        readiness_delta=Decimal("6.2"),
        outcome_status=InterventionOutcomeStatus.HIGHLY_EFFECTIVE,
    )
    assert explanation == "Revision Sprint interventions have historically improved readiness by 6.2 points."


def test_limited_effectiveness_explanation() -> None:
    explanation = explain_intervention_outcome_v1(
        intervention_type=TwinInterventionType.WEAKNESS_REMEDIATION,
        readiness_delta=Decimal("1.0"),
        outcome_status=InterventionOutcomeStatus.INEFFECTIVE,
    )
    assert explanation == "Weakness Remediation has shown limited effectiveness recently."
