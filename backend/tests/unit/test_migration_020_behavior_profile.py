"""Migration 020 behavior profile."""

from prepos.infrastructure.db.models.student import PreparationTwinModel


def test_preparation_twin_model_has_behavior_profile_columns() -> None:
    columns = {column.name for column in PreparationTwinModel.__table__.columns}
    assert "learning_style" in columns
    assert "risk_profile" in columns
    assert "consistency_score" in columns
    assert "discipline_score" in columns
    assert "engagement_score" in columns
