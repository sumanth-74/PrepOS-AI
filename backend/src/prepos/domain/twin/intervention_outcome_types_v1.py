from __future__ import annotations

from enum import StrEnum

INTERVENTION_OUTCOME_V1 = "intervention_outcome_v1"
INTERVENTION_BASELINE_V1 = "intervention_baseline_v1"
INTERVENTION_OPTIMIZER_V1 = "intervention_optimizer_v1"


class InterventionOutcomeStatus(StrEnum):
    HIGHLY_EFFECTIVE = "HIGHLY_EFFECTIVE"
    EFFECTIVE = "EFFECTIVE"
    PARTIALLY_EFFECTIVE = "PARTIALLY_EFFECTIVE"
    INEFFECTIVE = "INEFFECTIVE"
