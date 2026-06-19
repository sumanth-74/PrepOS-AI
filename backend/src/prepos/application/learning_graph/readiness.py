from __future__ import annotations

from prepos.domain.learning_graph.entities import LearningGraphReadinessSnapshot
from prepos.domain.scoring.readiness_drivers_v1 import ReadinessDriversV1, compute_readiness_drivers_v1
from prepos.domain.scoring.readiness_v1_1 import (
    ReadinessInputsV1_1,
    ReadinessResultV1_1,
    compute_readiness_v1_1,
)


def compute_readiness_from_snapshot(
    snapshot: LearningGraphReadinessSnapshot,
) -> tuple[ReadinessResultV1_1, ReadinessDriversV1 | None]:
    """Readiness Engine entry point; depends only on the LG snapshot port."""
    result = compute_readiness_v1_1(
        ReadinessInputsV1_1(
            average_mastery=snapshot.average_mastery,
            average_retention=snapshot.average_retention,
            average_confidence=snapshot.average_confidence,
            rated_node_count=snapshot.rated_node_count,
            total_node_count=snapshot.total_node_count,
        )
    )
    drivers = compute_readiness_drivers_v1(result)
    return result, drivers
