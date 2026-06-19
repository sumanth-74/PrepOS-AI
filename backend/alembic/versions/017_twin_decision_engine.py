"""Twin decision engine S7.0."""

from alembic import op
import sqlalchemy as sa

revision = "017_twin_decision_engine"
down_revision = "016_goal_engine"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "preparation_twins",
        sa.Column("decision_type", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "preparation_twins",
        sa.Column("decision_score", sa.Numeric(precision=5, scale=2), nullable=True),
    )
    op.add_column(
        "preparation_twins",
        sa.Column("expected_readiness_gain", sa.Numeric(precision=5, scale=2), nullable=True),
    )
    op.add_column(
        "preparation_twins",
        sa.Column("expected_score_gain", sa.Numeric(precision=5, scale=2), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("preparation_twins", "expected_score_gain")
    op.drop_column("preparation_twins", "expected_readiness_gain")
    op.drop_column("preparation_twins", "decision_score")
    op.drop_column("preparation_twins", "decision_type")
