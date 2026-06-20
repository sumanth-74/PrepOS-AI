"""Current affairs source metadata columns (P7 S18)."""

from alembic import op
import sqlalchemy as sa

revision = "030_current_affairs_metadata"
down_revision = "029_copilot_content_analytics"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "knowledge_sources",
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "knowledge_sources",
        sa.Column("source_authority", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "knowledge_sources",
        sa.Column("exam_stage", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "knowledge_sources",
        sa.Column("importance", sa.String(length=32), nullable=True),
    )
    op.create_index(
        "ix_knowledge_sources_published_at",
        "knowledge_sources",
        ["published_at"],
    )
    op.create_index(
        "ix_knowledge_sources_source_type_published",
        "knowledge_sources",
        ["source_type", "published_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_knowledge_sources_source_type_published", table_name="knowledge_sources")
    op.drop_index("ix_knowledge_sources_published_at", table_name="knowledge_sources")
    op.drop_column("knowledge_sources", "importance")
    op.drop_column("knowledge_sources", "exam_stage")
    op.drop_column("knowledge_sources", "source_authority")
    op.drop_column("knowledge_sources", "published_at")
