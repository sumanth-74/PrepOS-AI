"""Twin intervention engine S7.1."""

from alembic import op
import sqlalchemy as sa

revision = "018_twin_interventions"
down_revision = "017_twin_decision_engine"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "preparation_twins",
        sa.Column("intervention_type", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "preparation_twins",
        sa.Column("intervention_score", sa.Numeric(precision=5, scale=2), nullable=True),
    )
    op.add_column(
        "preparation_twins",
        sa.Column("intervention_urgency", sa.String(length=32), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("preparation_twins", "intervention_urgency")
    op.drop_column("preparation_twins", "intervention_score")
    op.drop_column("preparation_twins", "intervention_type")
