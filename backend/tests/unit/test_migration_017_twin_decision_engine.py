"""Migration 017 twin decision engine."""

from prepos.infrastructure.db.models.student import PreparationTwinModel


def test_preparation_twin_model_has_decision_columns() -> None:
    columns = {column.name for column in PreparationTwinModel.__table__.columns}
    assert "decision_type" in columns
    assert "decision_score" in columns
    assert "expected_readiness_gain" in columns
    assert "expected_score_gain" in columns
