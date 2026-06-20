from __future__ import annotations

from prepos.infrastructure.db.models.mentor_interventions import (
    InterventionEffectivenessModel,
    InterventionRecommendationModel,
    MentorInterventionModel,
)


def test_migration_040_models_have_expected_columns() -> None:
    intervention_columns = {column.name for column in MentorInterventionModel.__table__.columns}
    assert intervention_columns >= {
        "id",
        "tenant_id",
        "mentor_id",
        "student_id",
        "exam_id",
        "intervention_type",
        "concept_id",
        "reason",
        "predicted_gain",
        "priority_score",
        "status",
        "created_at",
    }

    effectiveness_columns = {column.name for column in InterventionEffectivenessModel.__table__.columns}
    assert effectiveness_columns >= {
        "id",
        "intervention_id",
        "readiness_before",
        "readiness_after",
        "actual_gain",
        "effectiveness_score",
        "evaluated_at",
    }

    recommendation_columns = {column.name for column in InterventionRecommendationModel.__table__.columns}
    assert recommendation_columns >= {
        "id",
        "tenant_id",
        "student_id",
        "exam_id",
        "intervention_type",
        "recommendation_reason",
        "impact_score",
        "confidence",
        "predicted_gain",
        "created_at",
    }


def test_mentor_interventions_migration_chain() -> None:
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    config = Config("alembic.ini")
    script = ScriptDirectory.from_config(config)
    revision = script.get_revision("040_mentor_interventions")
    assert revision is not None
    assert revision.down_revision == "039_goal_forecasting"
