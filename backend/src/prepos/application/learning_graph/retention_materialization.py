from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from prepos.domain.learning_graph.entities import ConceptProgressNode
from prepos.domain.learning_graph.policies import NodeStatus
from prepos.domain.scoring.retention_v1 import RetentionInputs, RetentionResult, compute_retention_v1


def materialize_node_retention(
    node: ConceptProgressNode,
    *,
    current_time: datetime | None = None,
) -> RetentionResult:
    """Single source of truth for on-read retention materialization."""
    now = current_time or datetime.now(UTC)
    return compute_retention_v1(
        RetentionInputs(
            mastery_score=node.mastery_score,
            retention_stability_s=node.retention_stability_s,
            retention_last_review_at=node.retention_last_review_at,
            retention_last_grade=node.retention_last_grade,
            current_time=now,
            node_state=node.node_state,
        )
    )


def materialized_retention_score(
    node: ConceptProgressNode,
    *,
    current_time: datetime | None = None,
) -> Decimal | None:
    return materialize_node_retention(node, current_time=current_time).value


def compute_due_for_revision(
    node: ConceptProgressNode,
    *,
    current_time: datetime | None = None,
) -> bool:
    """Node is due when rated, reviewed, and next_review_at <= now."""
    if node.node_state != NodeStatus.RATED:
        return False
    if node.retention_last_review_at is None:
        return False
    now = current_time or datetime.now(UTC)
    retention = materialize_node_retention(node, current_time=now)
    if retention.next_review_at is None:
        return False
    return retention.next_review_at <= now


def _importance_weighted_average(
    numerator: Decimal,
    denominator: Decimal,
) -> Decimal | None:
    if denominator == 0:
        return None
    return (numerator / denominator).quantize(Decimal("0.01"))


@dataclass(frozen=True, slots=True)
class GraphScoreAggregates:
    average_mastery: Decimal | None
    average_retention: Decimal | None
    average_confidence: Decimal | None
    rated_node_count: int


def compute_graph_score_aggregates(
    nodes: tuple[ConceptProgressNode, ...],
    *,
    current_time: datetime | None = None,
) -> GraphScoreAggregates:
    """Importance-weighted aggregates; retention uses materialized values at request time."""
    now = current_time or datetime.now(UTC)
    rated_nodes = [node for node in nodes if node.node_state == NodeStatus.RATED]

    mastery_numerator = Decimal("0")
    mastery_denominator = Decimal("0")
    retention_numerator = Decimal("0")
    retention_denominator = Decimal("0")
    confidence_numerator = Decimal("0")
    confidence_denominator = Decimal("0")

    for node in rated_nodes:
        importance = node.importance_score
        mastery_numerator += node.mastery_score * importance
        mastery_denominator += importance

        if node.confidence_score is not None:
            confidence_numerator += node.confidence_score * importance
            confidence_denominator += importance

        materialized = materialize_node_retention(node, current_time=now).value
        if materialized is not None:
            retention_numerator += materialized * importance
            retention_denominator += importance

    return GraphScoreAggregates(
        average_mastery=_importance_weighted_average(mastery_numerator, mastery_denominator),
        average_retention=_importance_weighted_average(retention_numerator, retention_denominator),
        average_confidence=_importance_weighted_average(confidence_numerator, confidence_denominator),
        rated_node_count=len(rated_nodes),
    )


def due_revision_sort_key(
    node: ConceptProgressNode,
    *,
    current_time: datetime | None = None,
) -> tuple[float, Decimal]:
    """Sort by overdue duration descending, then importance descending."""
    now = current_time or datetime.now(UTC)
    retention = materialize_node_retention(node, current_time=now)
    next_review_at = retention.next_review_at
    overdue_seconds = (now - next_review_at).total_seconds() if next_review_at is not None else 0.0
    return (-overdue_seconds, -node.importance_score)
