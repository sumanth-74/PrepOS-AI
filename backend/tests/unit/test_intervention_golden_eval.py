from __future__ import annotations

from prepos.application.interventions.intervention_engine import InterventionCandidateInput, compute_predicted_gain
from prepos.application.interventions.intervention_optimizer import optimize_interventions


def test_golden_intervention_ranking_for_one_hundred_students() -> None:
    for index in range(100):
        candidates = [
            {
                "concept_id": f"concept_{index % 7}",
                "concept_name": f"Concept {index % 7}",
                "weakness": 40.0 + (index % 10) * 5.0,
                "pyq_importance": 30.0 + (index % 8) * 4.0,
                "historical_failure": 20.0 + (index % 6) * 6.0,
                "forecast_risk": 50.0 + (index % 5) * 8.0,
            }
        ]
        forecast_risk = 45.0 + (index % 9) * 5.0
        memory_signal = 25.0 + (index % 4) * 10.0
        first = optimize_interventions(
            concept_candidates=candidates,
            forecast_risk=forecast_risk,
            memory_signal=memory_signal,
            limit=5,
        )
        second = optimize_interventions(
            concept_candidates=candidates,
            forecast_risk=forecast_risk,
            memory_signal=memory_signal,
            limit=5,
        )
        assert first == second
        priorities = [item.priority_score for item in first]
        assert priorities == sorted(priorities, reverse=True)

        low_minutes = InterventionCandidateInput(
            intervention_type="concept_revision",
            concept_id="concept_a",
            concept_name="Concept A",
            forecast_risk=40.0,
            weakness=50.0,
            historical_failure=30.0,
            pyq_importance=35.0,
            memory_signal=25.0,
        )
        high_minutes = InterventionCandidateInput(
            intervention_type="concept_revision",
            concept_id="concept_a",
            concept_name="Concept A",
            forecast_risk=80.0,
            weakness=85.0,
            historical_failure=60.0,
            pyq_importance=75.0,
            memory_signal=70.0,
        )
        assert compute_predicted_gain(high_minutes) >= compute_predicted_gain(low_minutes)
