from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from prepos.domain.scoring.confidence_v1 import ConfidenceInputs, compute_confidence_v1
from prepos.domain.scoring.importance_copy_v1 import ImportanceCopyInputs, compute_importance_copy_v1
from prepos.domain.scoring.mastery_nonmcq_v1 import compute_mastery_nonmcq_v1
from prepos.domain.scoring.mastery_v1 import MasteryEvidenceCounters, compute_mastery_v1
from prepos.domain.scoring.retention_v1 import RETENTION_V1, RetentionInputs, compute_retention_v1
from prepos.domain.scoring.weakness_v1 import WeaknessInputs, compute_weakness_v1


def test_mastery_v1_increases_with_strong_mcq_evidence() -> None:
    result = compute_mastery_v1(
        MasteryEvidenceCounters(
            mcq_component=Decimal("1"),
            n_mcq=5,
        )
    )

    assert result.version == "mastery_v1"
    assert result.value == Decimal("38.46")
    assert result.n_total == 5
    assert result.unrated is False
    assert result.active_components == ("mcq",)


def test_mastery_v1_decreases_with_weak_mcq_evidence() -> None:
    result = compute_mastery_v1(
        MasteryEvidenceCounters(
            mcq_component=Decimal("0.2"),
            n_mcq=5,
        )
    )

    assert result.value == Decimal("7.69")
    assert result.n_total == 5


def test_confidence_v1_increases_with_high_mcq_accuracy() -> None:
    result = compute_confidence_v1(
        ConfidenceInputs(
            n_mcq=5,
            mcq_accuracy_unit=Decimal("0.8"),
        )
    )

    assert result.version == "confidence_v1"
    assert result.value == Decimal("61.54")
    assert result.n_evidence == 5
    assert "self" in result.active_signals
    assert "consistency" in result.active_signals


def test_confidence_v1_decreases_with_low_mcq_accuracy() -> None:
    result = compute_confidence_v1(
        ConfidenceInputs(
            n_mcq=5,
            mcq_accuracy_unit=Decimal("0.2"),
        )
    )

    assert result.value == Decimal("38.46")


def test_mastery_nonmcq_v1_blends_non_mcq_channels() -> None:
    result = compute_mastery_nonmcq_v1(
        MasteryEvidenceCounters(
            mains_component=Decimal("0.8"),
            n_mains=3,
            revision_component=Decimal("0.6"),
            n_rev=2,
            study_component=Decimal("0.5"),
            n_study=1,
        )
    )

    assert result.version == "masterynonmcq_v1"
    assert result.value == Decimal("29.29")
    assert result.n_nonmcq == 6
    assert result.active_components == ("mains", "revision", "study")


def test_weakness_v1_on_demand_with_overconfidence_bonus() -> None:
    result = compute_weakness_v1(
        WeaknessInputs(
            mastery=Decimal("40"),
            retention=Decimal("30"),
            error_rate=Decimal("0.2"),
            confidence=Decimal("80"),
        )
    )

    assert result.version == "weakness_v1"
    assert result.value == Decimal("67.00")
    assert result.overconfident is True
    assert result.unrated is False


def test_weakness_v1_returns_unrated_when_flagged() -> None:
    result = compute_weakness_v1(WeaknessInputs(mastery=Decimal("50"), retention=Decimal("50"), unrated=True))

    assert result.value is None
    assert result.weakness_unit is None
    assert result.overconfident is False
    assert result.unrated is True


def test_retention_v1_unrated_node() -> None:
    result = compute_retention_v1(
        RetentionInputs(
            mastery_score=Decimal("50"),
            retention_stability_s=None,
            retention_last_review_at=None,
            retention_last_grade=None,
            current_time=datetime.now(UTC),
            node_state="unrated",
        )
    )

    assert result.version == RETENTION_V1
    assert result.value is None
    assert result.unrated is True


def test_retention_v1_materializes_from_review_state() -> None:
    review_at = datetime(2026, 1, 1, tzinfo=UTC)
    result = compute_retention_v1(
        RetentionInputs(
            mastery_score=Decimal("50"),
            retention_stability_s=Decimal("14"),
            retention_last_review_at=review_at,
            retention_last_grade=2,
            current_time=review_at,
            node_state="rated",
        )
    )

    assert result.value == Decimal("100.00")
    assert result.unrated is False
    assert result.next_review_at == review_at + timedelta(days=14)


def test_importance_copy_v1_stub_copies_global_importance() -> None:
    result = compute_importance_copy_v1(
        ImportanceCopyInputs(
            global_importance=Decimal("80"),
            optional_subject_match=True,
        )
    )

    assert result.version == "importance_copy_v1"
    assert result.value == Decimal("80.00")
    assert result.global_importance == Decimal("80.00")
    assert result.personalized is False


def test_importance_copy_v1_stub_applies_optional_multiplier() -> None:
    result = compute_importance_copy_v1(
        ImportanceCopyInputs(
            global_importance=Decimal("80"),
            optional_subject_match=False,
        )
    )

    assert result.value == Decimal("72.00")
    assert result.personalized is True
