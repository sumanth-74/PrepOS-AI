"""Migration 016 goal engine."""

from prepos.infrastructure.db.models.goal import StudentPreparationGoalModel


def test_student_preparation_goal_model_registered() -> None:
    assert StudentPreparationGoalModel.__tablename__ == "student_preparation_goals"
