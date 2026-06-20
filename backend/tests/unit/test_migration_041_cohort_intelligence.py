from __future__ import annotations

from prepos.infrastructure.db.models.cohort_intelligence import (
    CohortEventModel,
    CohortSnapshotModel,
    CohortTrendModel,
    StudentSegmentModel,
)


def test_migration_041_models_have_expected_columns() -> None:
    snapshot_columns = {column.name for column in CohortSnapshotModel.__table__.columns}
    assert snapshot_columns >= {
        "id",
        "tenant_id",
        "cohort_id",
        "snapshot_date",
        "student_count",
        "avg_readiness",
        "avg_forecast",
        "avg_effectiveness",
        "risk_count",
        "created_at",
    }

    segment_columns = {column.name for column in StudentSegmentModel.__table__.columns}
    assert segment_columns >= {
        "id",
        "tenant_id",
        "student_id",
        "segment_type",
        "segment_score",
        "calculated_at",
    }

    trend_columns = {column.name for column in CohortTrendModel.__table__.columns}
    assert trend_columns >= {
        "id",
        "tenant_id",
        "cohort_id",
        "concept_id",
        "trend_direction",
        "readiness_delta",
        "created_at",
    }

    event_columns = {column.name for column in CohortEventModel.__table__.columns}
    assert event_columns >= {"id", "tenant_id", "cohort_id", "event_type", "created_at"}


def test_cohort_intelligence_migration_chain() -> None:
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    config = Config("alembic.ini")
    script = ScriptDirectory.from_config(config)
    revision = script.get_revision("041_cohort_intelligence")
    assert revision is not None
    assert revision.down_revision == "040_mentor_interventions"
