"""Migration 018 twin interventions."""

from prepos.infrastructure.db.models.student import PreparationTwinModel


def test_preparation_twin_model_has_intervention_columns() -> None:
    columns = {column.name for column in PreparationTwinModel.__table__.columns}
    assert "intervention_type" in columns
    assert "intervention_score" in columns
    assert "intervention_urgency" in columns
