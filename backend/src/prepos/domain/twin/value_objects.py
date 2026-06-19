from __future__ import annotations

from enum import StrEnum


class RecommendationType(StrEnum):
    WEAKNESS_RECOVERY = "WEAKNESS_RECOVERY"
    REVISION_DUE = "REVISION_DUE"
    HIGH_IMPORTANCE_GAP = "HIGH_IMPORTANCE_GAP"
    READINESS_BOOST = "READINESS_BOOST"
