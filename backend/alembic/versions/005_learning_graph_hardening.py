"""Learning Graph S4.5 hardening: nullable retention, scoring versions, lifecycle rename."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "005_learning_graph_hardening"
down_revision = "004_learning_graph"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "student_concept_progress",
        sa.Column("mastery_version", sa.String(length=32), server_default="mastery_v1", nullable=False),
    )
    op.add_column(
        "student_concept_progress",
        sa.Column("mastery_nonmcq_version", sa.String(length=32), server_default="masterynonmcq_v1", nullable=False),
    )
    op.add_column(
        "student_concept_progress",
        sa.Column("retention_version", sa.String(length=32), server_default="retention_v1", nullable=False),
    )
    op.add_column(
        "student_concept_progress",
        sa.Column("confidence_version", sa.String(length=32), server_default="confidence_v1", nullable=False),
    )
    op.add_column(
        "student_concept_progress",
        sa.Column("importance_version", sa.String(length=32), server_default="importance_copy_v1", nullable=False),
    )

    op.execute(
        """
        UPDATE student_concept_progress
        SET retention_score = NULL
        WHERE status = 'unstarted' AND retention_score = 0
        """
    )

    op.alter_column(
        "student_concept_progress",
        "retention_score",
        existing_type=sa.Numeric(precision=5, scale=2),
        nullable=True,
    )

    op.execute(
        """
        UPDATE student_concept_progress
        SET status = 'unrated'
        WHERE status = 'unstarted'
        """
    )
    op.execute(
        """
        UPDATE student_concept_progress
        SET status = 'rated'
        WHERE status = 'active'
        """
    )

    op.drop_index(op.f("ix_student_concept_progress_status"), table_name="student_concept_progress")
    op.alter_column(
        "student_concept_progress",
        "status",
        new_column_name="node_state",
        existing_type=sa.String(length=32),
        existing_nullable=False,
    )
    op.create_index(
        op.f("ix_student_concept_progress_node_state"),
        "student_concept_progress",
        ["node_state"],
        unique=False,
    )

    op.add_column(
        "learning_graph_events",
        sa.Column("event_version", sa.Integer(), server_default="1", nullable=False),
    )
    op.add_column(
        "learning_graph_events",
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.add_column(
        "learning_graph_events",
        sa.Column(
            "recorded_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.add_column(
        "learning_graph_events",
        sa.Column(
            "scoring_versions",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=False,
        ),
    )

    op.execute(
        """
        UPDATE learning_graph_events
        SET occurred_at = created_at,
            recorded_at = created_at
        WHERE occurred_at IS NULL OR recorded_at IS NULL
        """
    )


def downgrade() -> None:
    op.drop_column("learning_graph_events", "scoring_versions")
    op.drop_column("learning_graph_events", "recorded_at")
    op.drop_column("learning_graph_events", "occurred_at")
    op.drop_column("learning_graph_events", "event_version")

    op.drop_index(op.f("ix_student_concept_progress_node_state"), table_name="student_concept_progress")
    op.alter_column(
        "student_concept_progress",
        "node_state",
        new_column_name="status",
        existing_type=sa.String(length=32),
        existing_nullable=False,
    )
    op.execute(
        """
        UPDATE student_concept_progress
        SET status = 'unstarted'
        WHERE status = 'unrated'
        """
    )
    op.execute(
        """
        UPDATE student_concept_progress
        SET status = 'active'
        WHERE status = 'rated'
        """
    )
    op.create_index(op.f("ix_student_concept_progress_status"), "student_concept_progress", ["status"], unique=False)

    op.execute(
        """
        UPDATE student_concept_progress
        SET retention_score = 0
        WHERE retention_score IS NULL
        """
    )
    op.alter_column(
        "student_concept_progress",
        "retention_score",
        existing_type=sa.Numeric(precision=5, scale=2),
        nullable=False,
        server_default="0",
    )

    op.drop_column("student_concept_progress", "importance_version")
    op.drop_column("student_concept_progress", "confidence_version")
    op.drop_column("student_concept_progress", "retention_version")
    op.drop_column("student_concept_progress", "mastery_nonmcq_version")
    op.drop_column("student_concept_progress", "mastery_version")
