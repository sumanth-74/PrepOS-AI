"""Twin S5.5: snapshot projection columns on preparation_twins."""

from alembic import op
import sqlalchemy as sa

revision = "010_twin_projection_snapshot"
down_revision = "009_revision_queue_projection"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "preparation_twins",
        sa.Column("readiness_score", sa.Numeric(precision=5, scale=2), nullable=True),
    )
    op.add_column(
        "preparation_twins",
        sa.Column("average_mastery", sa.Numeric(precision=5, scale=2), nullable=True),
    )
    op.add_column(
        "preparation_twins",
        sa.Column("average_retention", sa.Numeric(precision=5, scale=2), nullable=True),
    )
    op.add_column(
        "preparation_twins",
        sa.Column("average_confidence", sa.Numeric(precision=5, scale=2), nullable=True),
    )
    op.add_column(
        "preparation_twins",
        sa.Column("rated_node_count", sa.Integer(), nullable=True),
    )
    op.add_column(
        "preparation_twins",
        sa.Column("due_revision_count", sa.Integer(), nullable=True),
    )
    op.add_column(
        "preparation_twins",
        sa.Column("high_risk_concept_count", sa.Integer(), nullable=True),
    )
    op.add_column(
        "preparation_twins",
        sa.Column("largest_positive_driver", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "preparation_twins",
        sa.Column("largest_negative_driver", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "preparation_twins",
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("preparation_twins", "generated_at")
    op.drop_column("preparation_twins", "largest_negative_driver")
    op.drop_column("preparation_twins", "largest_positive_driver")
    op.drop_column("preparation_twins", "high_risk_concept_count")
    op.drop_column("preparation_twins", "due_revision_count")
    op.drop_column("preparation_twins", "rated_node_count")
    op.drop_column("preparation_twins", "average_confidence")
    op.drop_column("preparation_twins", "average_retention")
    op.drop_column("preparation_twins", "average_mastery")
    op.drop_column("preparation_twins", "readiness_score")
