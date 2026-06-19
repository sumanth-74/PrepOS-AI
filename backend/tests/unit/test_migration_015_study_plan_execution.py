"""Migration 015 study plan execution tracking."""

from prepos.infrastructure.db.models.study_plan_execution import StudentStudyPlanExecutionModel


def test_student_study_plan_execution_model_registered() -> None:
    assert StudentStudyPlanExecutionModel.__tablename__ == "student_study_plan_execution"
