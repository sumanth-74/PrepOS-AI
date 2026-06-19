"""Migration 023 mentor projection."""

from prepos.infrastructure.db.models.student import PreparationTwinModel


def test_preparation_twin_model_has_mentor_columns() -> None:
    columns = {column.name for column in PreparationTwinModel.__table__.columns}
    assert "mentor_status" in columns
    assert "top_mentor_message" in columns
