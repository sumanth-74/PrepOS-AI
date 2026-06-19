"""Learning Graph S4.6: nullable confidence_score for unrated nodes."""

from alembic import op
import sqlalchemy as sa

revision = "006_confidence_nullable"
down_revision = "005_learning_graph_hardening"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE student_concept_progress
        SET confidence_score = NULL
        WHERE node_state = 'unrated' AND confidence_score = 0
        """
    )
    op.alter_column(
        "student_concept_progress",
        "confidence_score",
        existing_type=sa.Numeric(precision=5, scale=2),
        nullable=True,
        server_default=None,
    )


def downgrade() -> None:
    op.execute(
        """
        UPDATE student_concept_progress
        SET confidence_score = 0
        WHERE confidence_score IS NULL
        """
    )
    op.alter_column(
        "student_concept_progress",
        "confidence_score",
        existing_type=sa.Numeric(precision=5, scale=2),
        nullable=False,
        server_default="0",
    )
