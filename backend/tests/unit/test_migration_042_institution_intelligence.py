from __future__ import annotations

from prepos.infrastructure.db.models.institution_intelligence import (
    InstitutionEventModel,
    InstitutionInsightModel,
    InstitutionRecommendationModel,
    InstitutionTrendModel,
)


def test_migration_042_models_have_expected_columns() -> None:
    insight_columns = {column.name for column in InstitutionInsightModel.__table__.columns}
    assert insight_columns >= {
        "id",
        "tenant_id",
        "insight_type",
        "insight_key",
        "title",
        "severity",
        "created_at",
    }

    recommendation_columns = {column.name for column in InstitutionRecommendationModel.__table__.columns}
    assert recommendation_columns >= {
        "id",
        "tenant_id",
        "recommendation_type",
        "title",
        "expected_impact",
        "affected_students",
        "priority_score",
        "created_at",
    }

    trend_columns = {column.name for column in InstitutionTrendModel.__table__.columns}
    assert trend_columns >= {
        "id",
        "tenant_id",
        "trend_type",
        "trend_key",
        "trend_direction",
        "delta_value",
        "period",
        "created_at",
    }

    event_columns = {column.name for column in InstitutionEventModel.__table__.columns}
    assert event_columns >= {"id", "tenant_id", "event_type", "created_at"}


def test_institution_intelligence_migration_chain() -> None:
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    config = Config("alembic.ini")
    script = ScriptDirectory.from_config(config)
    revision = script.get_revision("042_institution_intelligence")
    assert revision is not None
    assert revision.down_revision == "041_cohort_intelligence"
