"""Migration 021 personalization projection."""

from prepos.infrastructure.db.models.student import PreparationTwinModel


def test_preparation_twin_model_has_personalization_columns() -> None:
    columns = {column.name for column in PreparationTwinModel.__table__.columns}
    assert "best_activity_type" in columns
    assert "top_multiplier" in columns
    assert "historical_effectiveness" in columns
