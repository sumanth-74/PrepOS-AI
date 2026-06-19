"""Mentor case management S8.2."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "025_mentor_case_management"
down_revision = "024_mentor_action_center"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "mentor_cases",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("exam_id", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("priority", sa.String(length=32), nullable=False),
        sa.Column("mentor_action_type", sa.String(length=64), nullable=False),
        sa.Column("escalation_level", sa.String(length=32), nullable=False),
        sa.Column("mentor_action_priority", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolution_reason", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["exam_id"], ["exams.exam_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "student_id",
            "exam_id",
            "mentor_action_type",
            "status",
            name="uq_mentor_cases_open_action",
        ),
    )
    op.create_index("ix_mentor_cases_tenant_id", "mentor_cases", ["tenant_id"])
    op.create_index("ix_mentor_cases_tenant_status", "mentor_cases", ["tenant_id", "status"])
    op.create_index(
        "ix_mentor_cases_tenant_priority",
        "mentor_cases",
        ["tenant_id", "mentor_action_priority"],
    )

    op.create_table(
        "mentor_case_notes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("mentor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["mentor_cases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_mentor_case_notes_case_id", "mentor_case_notes", ["case_id"])
    op.create_index("ix_mentor_case_notes_mentor_id", "mentor_case_notes", ["mentor_id"])

    op.add_column(
        "preparation_twins",
        sa.Column("active_case_status", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "preparation_twins",
        sa.Column("active_case_priority", sa.String(length=32), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("preparation_twins", "active_case_priority")
    op.drop_column("preparation_twins", "active_case_status")
    op.drop_index("ix_mentor_case_notes_mentor_id", table_name="mentor_case_notes")
    op.drop_index("ix_mentor_case_notes_case_id", table_name="mentor_case_notes")
    op.drop_table("mentor_case_notes")
    op.drop_index("ix_mentor_cases_tenant_priority", table_name="mentor_cases")
    op.drop_index("ix_mentor_cases_tenant_status", table_name="mentor_cases")
    op.drop_index("ix_mentor_cases_tenant_id", table_name="mentor_cases")
    op.drop_table("mentor_cases")
