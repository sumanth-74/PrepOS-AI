from __future__ import annotations

from enum import StrEnum


class RevisionQueueStatus(StrEnum):
    SCHEDULED = "scheduled"
    DUE = "due"
    COMPLETED = "completed"
    DEPRECATED = "deprecated"
