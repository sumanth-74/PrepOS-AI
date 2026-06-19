from __future__ import annotations

from enum import StrEnum


class ActivityType(StrEnum):
    REVISION = "REVISION"
    WEAKNESS_RECOVERY = "WEAKNESS_RECOVERY"
    HIGH_IMPORTANCE_STUDY = "HIGH_IMPORTANCE_STUDY"
    READINESS_BOOST = "READINESS_BOOST"


class ExecutionStatus(StrEnum):
    COMPLETED = "COMPLETED"
    SKIPPED = "SKIPPED"
