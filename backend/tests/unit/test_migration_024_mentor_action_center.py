"""Migration 024 mentor action center."""

from prepos.infrastructure.db.models.student import PreparationTwinModel


def test_preparation_twin_model_has_mentor_action_columns() -> None:
    columns = {column.name for column in PreparationTwinModel.__table__.columns}
    assert "mentor_action_type" in columns
    assert "mentor_action_priority" in columns
    assert "escalation_level" in columns
