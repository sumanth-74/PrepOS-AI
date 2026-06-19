from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from prepos.domain.scoring.confidence_v1 import (
    ConfidenceInputs,
    compute_confidence_v1,
    compute_consistency_score,
    compute_speed_score,
    map_self_assessment,
)
from prepos.domain.scoring.config import DEFAULT_SCORING_CONFIG, ScoringConfig
from prepos.domain.scoring.mastery_nonmcq_v1 import compute_mastery_nonmcq_v1
from prepos.domain.scoring.mastery_v1 import (
    MasteryEvidenceCounters,
    McqAttemptEvidence,
    McqDifficulty,
    RecencyWeightedEvidence,
    build_mastery_evidence,
    compute_mastery_v1,
    compute_mcq_component,
    compute_recency_weighted_component,
    compute_study_component,
    difficulty_multiplier,
)
from prepos.domain.scoring.retention_v1 import (
    compute_retention_score_from_state,
    initialize_stability_from_mastery,
)
from prepos.domain.scoring.weakness_v1 import WeaknessInputs, compute_weakness_v1, is_overconfident


def test_mastery_component_helpers_cover_edge_paths() -> None:
    assert compute_mcq_component(()) == (Decimal("0"), 0)
    assert compute_recency_weighted_component(()) == (Decimal("0"), 0)
    assert compute_study_component(Decimal("0")) == Decimal("0")
    assert compute_study_component(Decimal("120")) > Decimal("0")

    assert difficulty_multiplier(McqDifficulty.EASY, DEFAULT_SCORING_CONFIG) < difficulty_multiplier(
        McqDifficulty.MEDIUM, DEFAULT_SCORING_CONFIG
    )
    assert difficulty_multiplier(McqDifficulty.HARD, DEFAULT_SCORING_CONFIG) > difficulty_multiplier(
        McqDifficulty.MEDIUM, DEFAULT_SCORING_CONFIG
    )


def test_mastery_mcq_component_uses_difficulty_and_recency() -> None:
    attempts = (
        McqAttemptEvidence(correct=True, difficulty=McqDifficulty.HARD, age_days=Decimal("0")),
        McqAttemptEvidence(correct=False, difficulty=McqDifficulty.EASY, age_days=Decimal("60")),
    )
    component, count = compute_mcq_component(attempts)
    assert count == 2
    assert Decimal("0") <= component <= Decimal("1")


def test_mastery_recency_weighted_component_averages_with_decay() -> None:
    evidences = (
        RecencyWeightedEvidence(value_unit=Decimal("1"), age_days=Decimal("0")),
        RecencyWeightedEvidence(value_unit=Decimal("0"), age_days=Decimal("90")),
    )
    component, count = compute_recency_weighted_component(evidences)
    assert count == 2
    assert Decimal("0") < component < Decimal("1")


def test_build_mastery_evidence_aggregates_all_channels() -> None:
    evidence = build_mastery_evidence(
        mcq_attempts=(McqAttemptEvidence(correct=True),),
        mains_evidences=(RecencyWeightedEvidence(value_unit=Decimal("0.7")),),
        revision_evidences=(RecencyWeightedEvidence(value_unit=Decimal("0.6")),),
        study_minutes=Decimal("30"),
        n_study_sessions=1,
    )
    assert evidence.n_mcq == 1
    assert evidence.n_mains == 1
    assert evidence.n_rev == 1
    assert evidence.n_study == 1


def test_mastery_v1_unrated_when_no_evidence() -> None:
    result = compute_mastery_v1(MasteryEvidenceCounters())
    assert result.unrated is True
    assert result.value == Decimal("0")
    assert result.active_components == ()


def test_mastery_components_return_zero_when_recency_weights_vanish() -> None:
    zero_recency_config = ScoringConfig(MASTERY_RECENCY_HALFLIFE_DAYS=Decimal("0"))
    attempts = (McqAttemptEvidence(correct=True, age_days=Decimal("10")),)
    assert compute_mcq_component(attempts, config=zero_recency_config) == (Decimal("0"), 1)

    evidences = (RecencyWeightedEvidence(value_unit=Decimal("0.8"), age_days=Decimal("10")),)
    assert compute_recency_weighted_component(evidences, config=zero_recency_config) == (Decimal("0"), 1)


def test_mastery_nonmcq_v1_unrated_without_non_mcq_evidence() -> None:
    result = compute_mastery_nonmcq_v1(MasteryEvidenceCounters(n_mcq=3, mcq_component=Decimal("0.9")))
    assert result.value is None
    assert result.n_nonmcq == 0


def test_confidence_helper_functions() -> None:
    assert map_self_assessment(Decimal("1")) == Decimal("0")
    assert map_self_assessment(Decimal("5")) == Decimal("100")
    assert compute_speed_score(Decimal("30"), Decimal("0")) == Decimal("0")
    assert compute_speed_score(Decimal("30"), Decimal("60")) == Decimal("50")
    assert compute_consistency_score((Decimal("50"),)) == Decimal("50")
    assert compute_consistency_score((Decimal("40"), Decimal("60"))) == Decimal("96.00")


def test_confidence_v1_uses_optional_signals() -> None:
    result = compute_confidence_v1(
        ConfidenceInputs(
            n_mcq=0,
            mcq_accuracy_unit=Decimal("0"),
            self_confidence=Decimal("80"),
            speed_score=Decimal("70"),
            self_assessment_values=(Decimal("60"), Decimal("62")),
        )
    )
    assert result.n_evidence == 2
    assert "self" in result.active_signals
    assert "speed" in result.active_signals
    assert "consistency" in result.active_signals


def test_confidence_v1_returns_prior_when_no_signals() -> None:
    result = compute_confidence_v1(ConfidenceInputs(n_mcq=0, mcq_accuracy_unit=Decimal("0")))
    assert result.value == Decimal("0")
    assert result.n_evidence == 0
    assert result.active_signals == ()


def test_retention_v1_applies_exponential_decay() -> None:
    review_at = datetime(2026, 1, 1, tzinfo=UTC)
    stability = initialize_stability_from_mastery(Decimal("80"))
    assert stability == Decimal("30")

    immediate = compute_retention_score_from_state(
        stability_s=stability,
        last_review_at=review_at,
        current_time=review_at,
    )
    later = compute_retention_score_from_state(
        stability_s=stability,
        last_review_at=review_at,
        current_time=review_at + timedelta(days=7),
    )

    assert immediate == Decimal("100.00")
    assert later < immediate


def test_weakness_not_overconfident_without_confidence() -> None:
    assert is_overconfident(mastery=Decimal("30"), confidence=None) is False


def test_weakness_v1_without_overconfidence_bonus() -> None:
    result = compute_weakness_v1(
        WeaknessInputs(
            mastery=Decimal("70"),
            retention=Decimal("60"),
            error_rate=Decimal("0.1"),
            confidence=Decimal("65"),
        )
    )
    assert result.overconfident is False
    assert result.value is not None
