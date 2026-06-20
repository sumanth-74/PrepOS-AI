"""Copilot content Q&A analytics fields (P7 S16.5)."""

from alembic import op
import sqlalchemy as sa

revision = "029_copilot_content_analytics"
down_revision = "028_knowledge_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "copilot_queries",
        sa.Column("citation_count", sa.Integer(), nullable=True),
    )
    op.add_column(
        "copilot_queries",
        sa.Column("confidence", sa.String(length=16), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("copilot_queries", "confidence")
    op.drop_column("copilot_queries", "citation_count")
