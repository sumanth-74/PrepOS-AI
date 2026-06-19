"""Migration 019 intervention outcomes."""

from prepos.infrastructure.db.models.student import StudentInterventionHistoryModel


def test_student_intervention_history_model_columns() -> None:
    columns = {column.name for column in StudentInterventionHistoryModel.__table__.columns}
    assert "intervention_type" in columns
    assert "effectiveness_score" in columns
    assert "readiness_delta" in columns
    assert "predicted_score_delta" in columns
    assert "completion_delta" in columns
    assert "outcome_status" in columns
    assert "created_at" in columns
