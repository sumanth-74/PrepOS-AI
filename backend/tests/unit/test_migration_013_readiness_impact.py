from __future__ import annotations

from prepos.infrastructure.db.models.study_plan import StudentStudyPlanModel
from prepos.infrastructure.db.models.twin import PreparationTwinRecommendationModel


def test_recommendation_model_has_readiness_gain_column() -> None:
    columns = PreparationTwinRecommendationModel.__table__.columns
    assert "readiness_gain" in columns


def test_student_study_plan_model_registered() -> None:
    assert StudentStudyPlanModel.__tablename__ == "student_study_plans"
