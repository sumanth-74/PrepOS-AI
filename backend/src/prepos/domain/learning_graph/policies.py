from __future__ import annotations

from decimal import Decimal

from prepos.domain.learning_graph.entities import ConceptProgressNode


class NodeStatus:
    UNRATED = "unrated"
    RATED = "rated"
    DEPRECATED = "deprecated"

    # Backward-compatible aliases (deprecated — use UNRATED / RATED)
    UNSTARTED = UNRATED
    ACTIVE = RATED


class LearningGraphPolicy:
    MIN_SCORE = Decimal("0")
    MAX_SCORE = Decimal("100")
    DEFAULT_IMPORTANCE = Decimal("50.00")
    OVERCONFIDENCE_GAP = Decimal("25")
    OVERCONFIDENCE_MASTERY_CEILING = Decimal("70")

    @classmethod
    def validate_score(cls, value: Decimal, *, field: str) -> None:
        if value < cls.MIN_SCORE or value > cls.MAX_SCORE:
            from prepos.domain.learning_graph.exceptions import LearningGraphDomainError

            raise LearningGraphDomainError(
                f"{field} must be between 0 and 100.",
                details={"field": field, "value": str(value)},
            )

    @classmethod
    def compute_overconfidence_flag(cls, *, mastery: Decimal, confidence: Decimal) -> bool:
        return (
            confidence - mastery >= cls.OVERCONFIDENCE_GAP
            and mastery < cls.OVERCONFIDENCE_MASTERY_CEILING
        )

    @classmethod
    def can_mutate(cls, node: ConceptProgressNode) -> bool:
        return node.node_state != NodeStatus.DEPRECATED

    @classmethod
    def transition_on_evidence(cls, node: ConceptProgressNode) -> str:
        if node.node_state == NodeStatus.UNRATED:
            return NodeStatus.RATED
        return node.node_state
