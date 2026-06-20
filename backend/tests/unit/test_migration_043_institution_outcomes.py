from __future__ import annotations

from prepos.infrastructure.db.models.institution_outcomes import (
    InstitutionInitiativeEffectivenessModel,
    InstitutionInitiativeModel,
    InstitutionOutcomeModel,
    InstitutionRoiMetricModel,
)


def test_migration_043_models_have_expected_columns() -> None:
    initiative_columns = {column.name for column in InstitutionInitiativeModel.__table__.columns}
    assert initiative_columns >= {
        "id",
        "tenant_id",
        "initiative_type",
        "title",
        "status",
        "start_date",
        "affected_students",
        "created_at",
    }

    outcome_columns = {column.name for column in InstitutionOutcomeModel.__table__.columns}
    assert outcome_columns >= {
        "id",
        "tenant_id",
        "outcome_type",
        "subject_key",
        "actual_gain",
        "expected_gain",
        "variance",
        "created_at",
    }

    roi_columns = {column.name for column in InstitutionRoiMetricModel.__table__.columns}
    assert roi_columns >= {
        "id",
        "tenant_id",
        "roi_score",
        "readiness_gain",
        "forecast_gain",
        "created_at",
    }

    effectiveness_columns = {
        column.name for column in InstitutionInitiativeEffectivenessModel.__table__.columns
    }
    assert effectiveness_columns >= {
        "id",
        "tenant_id",
        "initiative_id",
        "effectiveness_score",
        "status",
        "measured_at",
    }


def test_institution_outcomes_migration_chains_to_agent_framework() -> None:
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    config = Config("alembic.ini")
    script = ScriptDirectory.from_config(config)
    revision = script.get_revision("043_institution_outcomes")
    assert revision is not None
    assert revision.down_revision == "042_institution_intelligence"
    next_revision = script.get_revision("044_agent_execution_framework")
    assert next_revision is not None
    assert next_revision.down_revision == "043_institution_outcomes"
