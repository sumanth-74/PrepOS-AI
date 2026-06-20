from __future__ import annotations

import pytest

from prepos.application.interventions.intervention_effectiveness import (
    compute_actual_gain,
    compute_effectiveness_score,
)
from prepos.application.interventions.intervention_engine import (
    InterventionCandidateInput,
    compute_predicted_gain,
    compute_priority_score,
    normalize_score,
)
from prepos.application.interventions.intervention_explainer import explain_intervention
from prepos.application.interventions.intervention_models import InterventionScoreBreakdown
from prepos.application.interventions.intervention_optimizer import optimize_interventions, rank_intervention_candidate


def test_priority_score_weights_sum_to_normalized_score() -> None:
    inputs = InterventionCandidateInput(
        intervention_type="concept_revision",
        concept_id="polity_federalism",
        concept_name="Federalism",
        forecast_risk=80.0,
        weakness=75.0,
        historical_failure=60.0,
        pyq_importance=70.0,
        memory_signal=55.0,
    )
    priority, breakdown = compute_priority_score(inputs)
    expected = (
        breakdown["forecast_risk"] * 0.30
        + breakdown["weakness"] * 0.25
        + breakdown["historical_failure"] * 0.20
        + breakdown["pyq_importance"] * 0.15
        + breakdown["memory_signal"] * 0.10
    )
    assert priority == pytest.approx(expected, rel=1e-3)
    assert 0 <= priority <= 100


def test_predicted_gain_is_deterministic() -> None:
    inputs = InterventionCandidateInput(
        intervention_type="concept_revision",
        concept_id="polity_federalism",
        concept_name="Federalism",
        forecast_risk=70.0,
        weakness=80.0,
        historical_failure=40.0,
        pyq_importance=65.0,
        memory_signal=50.0,
    )
    assert compute_predicted_gain(inputs) == compute_predicted_gain(inputs)


def test_effectiveness_score_matches_actual_over_predicted() -> None:
    actual = compute_actual_gain(readiness_before=62.0, readiness_after=65.2)
    score = compute_effectiveness_score(predicted_gain=3.2, actual_gain=actual)
    assert actual == pytest.approx(3.2, abs=0.01)
    assert score == pytest.approx(100.0, abs=0.1)


def test_optimizer_ranking_is_stable() -> None:
    candidates = [
        {
            "concept_id": "polity_federalism",
            "concept_name": "Federalism",
            "weakness": 85.0,
            "pyq_importance": 70.0,
            "historical_failure": 55.0,
            "forecast_risk": 75.0,
        },
        {
            "concept_id": "polity_parliament",
            "concept_name": "Parliament",
            "weakness": 70.0,
            "pyq_importance": 60.0,
            "historical_failure": 40.0,
            "forecast_risk": 65.0,
        },
    ]
    first = optimize_interventions(
        concept_candidates=candidates,
        forecast_risk=75.0,
        memory_signal=50.0,
        limit=5,
    )
    second = optimize_interventions(
        concept_candidates=candidates,
        forecast_risk=75.0,
        memory_signal=50.0,
        limit=5,
    )
    assert first == second
    assert first[0].priority_score >= first[-1].priority_score


def test_explanation_includes_score_breakdown() -> None:
    inputs = InterventionCandidateInput(
        intervention_type="pyq_revision",
        concept_id="gs2_federalism",
        concept_name="Federalism",
        forecast_risk=65.0,
        weakness=72.0,
        historical_failure=45.0,
        pyq_importance=88.0,
        memory_signal=40.0,
    )
    ranked = rank_intervention_candidate(inputs)
    lines = explain_intervention(
        intervention_type=ranked.intervention_type,
        concept=ranked.concept_name,
        reason=ranked.reason,
        predicted_gain=ranked.predicted_gain,
        priority_score=ranked.priority_score,
        score_breakdown=ranked.score_breakdown,
        forecast_improvement=ranked.forecast_improvement,
    )
    assert any("Priority score" in line for line in lines)
    assert any("Predicted readiness gain" in line for line in lines)


def test_normalize_score_clamps() -> None:
    assert normalize_score(-5) == 0.0
    assert normalize_score(150) == 100.0
