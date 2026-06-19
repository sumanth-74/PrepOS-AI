"""Migration 025 mentor case management."""

from prepos.infrastructure.db.models.mentor_case import MentorCaseModel, MentorCaseNoteModel
from prepos.infrastructure.db.models.student import PreparationTwinModel


def test_mentor_case_models_exist() -> None:
    case_columns = {column.name for column in MentorCaseModel.__table__.columns}
    note_columns = {column.name for column in MentorCaseNoteModel.__table__.columns}
    assert "mentor_action_priority" in case_columns
    assert "resolution_reason" in case_columns
    assert "note" in note_columns


def test_preparation_twin_model_has_active_case_columns() -> None:
    columns = {column.name for column in PreparationTwinModel.__table__.columns}
    assert "active_case_status" in columns
    assert "active_case_priority" in columns
