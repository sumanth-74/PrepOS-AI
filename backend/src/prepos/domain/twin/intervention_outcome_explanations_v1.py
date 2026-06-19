from __future__ import annotations

from decimal import Decimal

from prepos.domain.scoring.common import round_score
from prepos.domain.twin.intervention_outcome_types_v1 import InterventionOutcomeStatus
from prepos.domain.twin.intervention_types_v1 import TwinInterventionType

INTERVENTION_OUTCOME_EXPLANATIONS_V1 = "intervention_outcome_explanations_v1"

_INTERVENTION_LABELS: dict[TwinInterventionType, str] = {
    TwinInterventionType.REVISION_SPRINT: "Revision Sprint",
    TwinInterventionType.WEAKNESS_REMEDIATION: "Weakness Remediation",
    TwinInterventionType.COVERAGE_RECOVERY: "Coverage Recovery",
    TwinInterventionType.CAPACITY_INCREASE: "Capacity Increase",
    TwinInterventionType.CAPACITY_REDUCTION: "Capacity Reduction",
    TwinInterventionType.MOCK_TEST: "Mock Test",
    TwinInterventionType.MAINTAIN_COURSE: "Maintain Course",
}


def _format_delta(value: Decimal) -> str:
    return f"{round_score(value):.2f}".rstrip("0").rstrip(".")


def _label(intervention_type: TwinInterventionType) -> str:
    return _INTERVENTION_LABELS.get(intervention_type, intervention_type.value.replace("_", " ").title())


def explain_intervention_outcome_v1(
    *,
    intervention_type: TwinInterventionType,
    readiness_delta: Decimal,
    outcome_status: InterventionOutcomeStatus,
) -> str:
    label = _label(intervention_type)
    delta = _format_delta(readiness_delta)
    if outcome_status in {
        InterventionOutcomeStatus.HIGHLY_EFFECTIVE,
        InterventionOutcomeStatus.EFFECTIVE,
    }:
        return f"{label} interventions have historically improved readiness by {delta} points."
    if outcome_status == InterventionOutcomeStatus.PARTIALLY_EFFECTIVE:
        return f"{label} has shown mixed effectiveness recently."
    return f"{label} has shown limited effectiveness recently."
