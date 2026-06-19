"""Study plan execution tracking S6.5."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "015_study_plan_execution_tracking"
down_revision = "014_study_plan_projection"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "student_study_plan_execution",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("exam_id", sa.String(length=64), nullable=False),
        sa.Column("concept_id", sa.String(length=128), nullable=False),
        sa.Column("activity_type", sa.String(length=32), nullable=False),
        sa.Column("planned_minutes", sa.Integer(), nullable=False),
        sa.Column("actual_minutes", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["exam_id"], ["exams.exam_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_student_study_plan_execution_tenant_id",
        "student_study_plan_execution",
        ["tenant_id"],
    )
    op.create_index(
        "ix_student_study_plan_execution_student_id",
        "student_study_plan_execution",
        ["student_id"],
    )
    op.create_index(
        "ix_student_study_plan_execution_exam_id",
        "student_study_plan_execution",
        ["exam_id"],
    )
    op.create_index(
        "ix_student_study_plan_execution_concept_id",
        "student_study_plan_execution",
        ["concept_id"],
    )
    op.create_index(
        "ix_student_study_plan_execution_completed_at",
        "student_study_plan_execution",
        ["completed_at"],
    )
    op.create_index(
        "ix_student_study_plan_execution_tenant_student_exam",
        "student_study_plan_execution",
        ["tenant_id", "student_id", "exam_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_student_study_plan_execution_tenant_student_exam",
        table_name="student_study_plan_execution",
    )
    op.drop_index(
        "ix_student_study_plan_execution_completed_at",
        table_name="student_study_plan_execution",
    )
    op.drop_index(
        "ix_student_study_plan_execution_concept_id",
        table_name="student_study_plan_execution",
    )
    op.drop_index(
        "ix_student_study_plan_execution_exam_id",
        table_name="student_study_plan_execution",
    )
    op.drop_index(
        "ix_student_study_plan_execution_student_id",
        table_name="student_study_plan_execution",
    )
    op.drop_index(
        "ix_student_study_plan_execution_tenant_id",
        table_name="student_study_plan_execution",
    )
    op.drop_table("student_study_plan_execution")
