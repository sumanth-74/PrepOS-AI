from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TwinProjectionMetrics:
    rebuild_count: int
    skipped_rebuild_count: int
    incremental_update_count: int
    lock_contention_count: int
