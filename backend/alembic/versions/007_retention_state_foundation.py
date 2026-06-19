"""Learning Graph S5.0: retention state columns and nullable score audit new_value."""

from alembic import op
import sqlalchemy as sa

revision = "007_retention_state_foundation"
down_revision = "006_confidence_nullable"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "student_concept_progress",
        sa.Column("retention_stability_s", sa.Numeric(precision=12, scale=4), nullable=True),
    )
    op.add_column(
        "student_concept_progress",
        sa.Column("retention_last_event_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "student_concept_progress",
        sa.Column("retention_last_review_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "student_concept_progress",
        sa.Column("retention_last_grade", sa.Integer(), nullable=True),
    )
    op.alter_column(
        "score_audit_log",
        "new_value",
        existing_type=sa.Numeric(precision=5, scale=2),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "score_audit_log",
        "new_value",
        existing_type=sa.Numeric(precision=5, scale=2),
        nullable=False,
    )
    op.drop_column("student_concept_progress", "retention_last_grade")
    op.drop_column("student_concept_progress", "retention_last_review_at")
    op.drop_column("student_concept_progress", "retention_last_event_at")
    op.drop_column("student_concept_progress", "retention_stability_s")
