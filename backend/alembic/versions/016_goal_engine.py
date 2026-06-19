"""Goal engine S6.6."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "016_goal_engine"
down_revision = "015_study_plan_execution_tracking"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "student_preparation_goals",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("exam_id", sa.String(length=64), nullable=False),
        sa.Column("target_readiness_score", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("target_date", sa.Date(), nullable=False),
        sa.Column("daily_capacity_minutes", sa.Integer(), nullable=False, server_default="120"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["exam_id"], ["exams.exam_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "student_id",
            "exam_id",
            name="uq_student_preparation_goals_tenant_student_exam",
        ),
    )
    op.create_index(
        "ix_student_preparation_goals_tenant_id",
        "student_preparation_goals",
        ["tenant_id"],
    )
    op.create_index(
        "ix_student_preparation_goals_student_id",
        "student_preparation_goals",
        ["student_id"],
    )
    op.create_index(
        "ix_student_preparation_goals_exam_id",
        "student_preparation_goals",
        ["exam_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_student_preparation_goals_exam_id", table_name="student_preparation_goals")
    op.drop_index("ix_student_preparation_goals_student_id", table_name="student_preparation_goals")
    op.drop_index("ix_student_preparation_goals_tenant_id", table_name="student_preparation_goals")
    op.drop_table("student_preparation_goals")
