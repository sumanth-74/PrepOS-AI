"""Revision queue S5.5: durable per-concept revision scheduling projection."""

from alembic import op
import sqlalchemy as sa

revision = "009_revision_queue_projection"
down_revision = "008_twin_recommendations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "student_revision_queue",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("student_id", sa.UUID(), nullable=False),
        sa.Column("exam_id", sa.String(length=64), nullable=False),
        sa.Column("concept_id", sa.String(length=128), nullable=False),
        sa.Column("next_review_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("retention_score", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("importance_score", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("weakness_score", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("priority_score", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["exam_id"], ["exams.exam_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "student_id",
            "concept_id",
            name="uq_student_revision_queue_tenant_student_concept",
        ),
    )
    op.create_index("ix_student_revision_queue_tenant_id", "student_revision_queue", ["tenant_id"])
    op.create_index("ix_student_revision_queue_student_id", "student_revision_queue", ["student_id"])
    op.create_index("ix_student_revision_queue_exam_id", "student_revision_queue", ["exam_id"])
    op.create_index(
        "ix_student_revision_queue_student_next_review",
        "student_revision_queue",
        ["student_id", "next_review_at"],
    )
    op.create_index(
        "ix_student_revision_queue_student_priority",
        "student_revision_queue",
        ["student_id", "priority_score"],
    )


def downgrade() -> None:
    op.drop_index("ix_student_revision_queue_student_priority", table_name="student_revision_queue")
    op.drop_index("ix_student_revision_queue_student_next_review", table_name="student_revision_queue")
    op.drop_index("ix_student_revision_queue_exam_id", table_name="student_revision_queue")
    op.drop_index("ix_student_revision_queue_student_id", table_name="student_revision_queue")
    op.drop_index("ix_student_revision_queue_tenant_id", table_name="student_revision_queue")
    op.drop_table("student_revision_queue")
