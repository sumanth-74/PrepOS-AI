"""Intervention outcomes S7.2."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "019_intervention_outcomes"
down_revision = "018_twin_interventions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "student_intervention_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("exam_id", sa.String(length=64), nullable=False),
        sa.Column("intervention_type", sa.String(length=64), nullable=False),
        sa.Column("effectiveness_score", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("readiness_delta", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("predicted_score_delta", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("completion_delta", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("outcome_status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["exam_id"], ["exams.exam_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_student_intervention_history_student_created",
        "student_intervention_history",
        ["student_id", "created_at"],
    )
    op.create_index(
        "ix_student_intervention_history_student_type",
        "student_intervention_history",
        ["student_id", "intervention_type"],
    )
    op.create_index(
        "ix_student_intervention_history_tenant_id",
        "student_intervention_history",
        ["tenant_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_student_intervention_history_tenant_id", table_name="student_intervention_history")
    op.drop_index("ix_student_intervention_history_student_type", table_name="student_intervention_history")
    op.drop_index("ix_student_intervention_history_student_created", table_name="student_intervention_history")
    op.drop_table("student_intervention_history")
