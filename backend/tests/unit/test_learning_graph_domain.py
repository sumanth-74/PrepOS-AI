from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from prepos.domain.learning_graph.entities import ConceptProgressNode
from prepos.domain.learning_graph.exceptions import LearningGraphDomainError, OptimisticLockFailureError
from prepos.domain.learning_graph.policies import LearningGraphPolicy, NodeStatus
from prepos.domain.scoring.confidence_v1 import CONFIDENCE_V1
from prepos.domain.scoring.importance_copy_v1 import IMPORTANCE_COPY_V1
from prepos.domain.scoring.mastery_nonmcq_v1 import MASTERY_NONMCQ_V1
from prepos.domain.scoring.mastery_v1 import MASTERY_V1
from prepos.domain.scoring.retention_v1 import RETENTION_V1


def _node(*, node_state: str = NodeStatus.UNRATED) -> ConceptProgressNode:
    now = datetime.now(UTC)
    return ConceptProgressNode(
        id=uuid4(),
        tenant_id=uuid4(),
        student_id=uuid4(),
        exam_id="upsc_cse",
        catalog_version="1.0.0",
        concept_id="history.ancient.indus_valley",
        subject_id="history",
        topic_id="history.ancient",
        mastery_score=Decimal("0"),
        mastery_nonmcq_score=Decimal("0"),
        retention_score=None,
        confidence_score=None,
        importance_score=Decimal("50"),
        overconfidence_flag=False,
        mcq_attempt_count=0,
        mcq_correct_count=0,
        nonmcq_attempt_count=0,
        revision_count=0,
        study_minutes=0,
        node_state=node_state,
        mastery_version=MASTERY_V1,
        mastery_nonmcq_version=MASTERY_NONMCQ_V1,
        retention_version=RETENTION_V1,
        confidence_version=CONFIDENCE_V1,
        importance_version=IMPORTANCE_COPY_V1,
        first_seen_at=now,
        last_activity_at=None,
        row_version=1,
    )


def test_learning_graph_policy_validates_score_bounds() -> None:
    LearningGraphPolicy.validate_score(Decimal("0"), field="mastery_score")
    LearningGraphPolicy.validate_score(Decimal("100"), field="mastery_score")

    with pytest.raises(LearningGraphDomainError, match="must be between 0 and 100"):
        LearningGraphPolicy.validate_score(Decimal("-1"), field="mastery_score")

    with pytest.raises(LearningGraphDomainError, match="must be between 0 and 100"):
        LearningGraphPolicy.validate_score(Decimal("101"), field="confidence_score")


def test_learning_graph_policy_blocks_deprecated_node_mutation() -> None:
    deprecated = _node(node_state=NodeStatus.DEPRECATED)
    rated = _node(node_state=NodeStatus.RATED)

    assert LearningGraphPolicy.can_mutate(deprecated) is False
    assert LearningGraphPolicy.can_mutate(rated) is True


def test_node_state_transitions_on_first_evidence() -> None:
    unrated = _node(node_state=NodeStatus.UNRATED)
    rated = _node(node_state=NodeStatus.RATED)
    deprecated = _node(node_state=NodeStatus.DEPRECATED)

    assert LearningGraphPolicy.transition_on_evidence(unrated) == NodeStatus.RATED
    assert LearningGraphPolicy.transition_on_evidence(rated) == NodeStatus.RATED
    assert LearningGraphPolicy.transition_on_evidence(deprecated) == NodeStatus.DEPRECATED


def test_node_status_backward_compatible_aliases() -> None:
    assert NodeStatus.UNSTARTED == NodeStatus.UNRATED
    assert NodeStatus.ACTIVE == NodeStatus.RATED


def test_learning_graph_policy_detects_overconfidence() -> None:
    assert (
        LearningGraphPolicy.compute_overconfidence_flag(
            mastery=Decimal("40"),
            confidence=Decimal("80"),
        )
        is True
    )
    assert (
        LearningGraphPolicy.compute_overconfidence_flag(
            mastery=Decimal("40"),
            confidence=Decimal("60"),
        )
        is False
    )
    assert (
        LearningGraphPolicy.compute_overconfidence_flag(
            mastery=Decimal("75"),
            confidence=Decimal("100"),
        )
        is False
    )


def test_optimistic_lock_failure_error_is_conflict_type() -> None:
    error = OptimisticLockFailureError(
        "Concurrent graph update conflict.",
        details={"expected_row_version": 1},
    )

    assert error.code == "OPTIMISTIC_LOCK"
    assert error.details["expected_row_version"] == 1
