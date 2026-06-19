"""Exam domain catalog tables."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "002_exam_domain"
down_revision = "001_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "exams",
        sa.Column("exam_id", sa.String(length=64), nullable=False),
        sa.Column("exam_code", sa.String(length=64), nullable=False),
        sa.Column("exam_name", sa.String(length=512), nullable=False),
        sa.Column("exam_type", sa.String(length=64), nullable=False),
        sa.Column("prelims_weight", sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column("mains_weight", sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column("interview_weight", sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column("domain_catalog_version", sa.String(length=32), nullable=False),
        sa.Column("essay_included", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("exam_id", name=op.f("pk_exams")),
        sa.UniqueConstraint("exam_code", name=op.f("uq_exams_exam_code")),
    )
    op.create_index(op.f("ix_exams_exam_code"), "exams", ["exam_code"], unique=False)
    op.create_index(op.f("ix_exams_status"), "exams", ["status"], unique=False)

    op.create_table(
        "exam_tracks",
        sa.Column("track_id", sa.String(length=128), nullable=False),
        sa.Column("exam_id", sa.String(length=64), nullable=False),
        sa.Column("track_code", sa.String(length=64), nullable=False),
        sa.Column("track_name", sa.String(length=255), nullable=False),
        sa.Column("stage", sa.String(length=32), nullable=False),
        sa.Column("subject_ids", postgresql.ARRAY(sa.String(length=128)), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["exam_id"], ["exams.exam_id"], name=op.f("fk_exam_tracks_exam_id_exams"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("track_id", name=op.f("pk_exam_tracks")),
        sa.UniqueConstraint("exam_id", "track_code", name="uq_exam_tracks_exam_code"),
    )
    op.create_index(op.f("ix_exam_tracks_exam_id"), "exam_tracks", ["exam_id"], unique=False)
    op.create_index(op.f("ix_exam_tracks_stage"), "exam_tracks", ["stage"], unique=False)
    op.create_index(op.f("ix_exam_tracks_track_code"), "exam_tracks", ["track_code"], unique=False)
    op.create_index("ix_exam_tracks_exam_id_status", "exam_tracks", ["exam_id", "status"], unique=False)

    op.create_table(
        "subjects",
        sa.Column("subject_id", sa.String(length=128), nullable=False),
        sa.Column("exam_id", sa.String(length=64), nullable=False),
        sa.Column("subject_name", sa.String(length=255), nullable=False),
        sa.Column("subject_slug", sa.String(length=128), nullable=False),
        sa.Column("prelims_applicable", sa.Boolean(), nullable=False),
        sa.Column("mains_applicable", sa.Boolean(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["exam_id"], ["exams.exam_id"], name=op.f("fk_subjects_exam_id_exams"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("subject_id", name=op.f("pk_subjects")),
    )
    op.create_index(op.f("ix_subjects_exam_id"), "subjects", ["exam_id"], unique=False)
    op.create_index(op.f("ix_subjects_status"), "subjects", ["status"], unique=False)
    op.create_index("ix_subjects_exam_id_sort_order", "subjects", ["exam_id", "sort_order"], unique=False)
    op.create_index("ix_subjects_exam_id_status", "subjects", ["exam_id", "status"], unique=False)

    op.create_table(
        "topics",
        sa.Column("topic_id", sa.String(length=192), nullable=False),
        sa.Column("exam_id", sa.String(length=64), nullable=False),
        sa.Column("subject_id", sa.String(length=128), nullable=False),
        sa.Column("topic_name", sa.String(length=255), nullable=False),
        sa.Column("topic_slug", sa.String(length=128), nullable=False),
        sa.Column("prelims_relevance", sa.Integer(), nullable=False),
        sa.Column("mains_relevance", sa.Integer(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("prelims_relevance >= 0 AND prelims_relevance <= 100", name="ck_topics_prelims_relevance"),
        sa.CheckConstraint("mains_relevance >= 0 AND mains_relevance <= 100", name="ck_topics_mains_relevance"),
        sa.ForeignKeyConstraint(["exam_id"], ["exams.exam_id"], name=op.f("fk_topics_exam_id_exams"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.subject_id"], name=op.f("fk_topics_subject_id_subjects"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("topic_id", name=op.f("pk_topics")),
    )
    op.create_index(op.f("ix_topics_exam_id"), "topics", ["exam_id"], unique=False)
    op.create_index(op.f("ix_topics_status"), "topics", ["status"], unique=False)
    op.create_index(op.f("ix_topics_subject_id"), "topics", ["subject_id"], unique=False)
    op.create_index("ix_topics_exam_id_status", "topics", ["exam_id", "status"], unique=False)
    op.create_index("ix_topics_subject_id_status", "topics", ["subject_id", "status"], unique=False)

    op.create_table(
        "catalog_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("exam_id", sa.String(length=64), nullable=False),
        sa.Column("version", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("published_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("concepts_added", sa.Integer(), nullable=False),
        sa.Column("concepts_deprecated", sa.Integer(), nullable=False),
        sa.Column("change_summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["exam_id"], ["exams.exam_id"], name=op.f("fk_catalog_versions_exam_id_exams"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_catalog_versions")),
        sa.UniqueConstraint("exam_id", "version", name="uq_catalog_versions_exam_version"),
    )
    op.create_index(op.f("ix_catalog_versions_exam_id"), "catalog_versions", ["exam_id"], unique=False)
    op.create_index(op.f("ix_catalog_versions_status"), "catalog_versions", ["status"], unique=False)
    op.create_index("ix_catalog_versions_exam_id_status", "catalog_versions", ["exam_id", "status"], unique=False)

    op.create_table(
        "concepts",
        sa.Column("concept_id", sa.String(length=256), nullable=False),
        sa.Column("exam_id", sa.String(length=64), nullable=False),
        sa.Column("subject_id", sa.String(length=128), nullable=False),
        sa.Column("topic_id", sa.String(length=192), nullable=False),
        sa.Column("parent_concept_id", sa.String(length=256), nullable=True),
        sa.Column("concept_name", sa.String(length=512), nullable=False),
        sa.Column("concept_slug", sa.String(length=128), nullable=False),
        sa.Column("concept_type", sa.String(length=64), nullable=False),
        sa.Column("prelims_relevance", sa.Integer(), nullable=False),
        sa.Column("mains_relevance", sa.Integer(), nullable=False),
        sa.Column("interview_relevance", sa.Integer(), nullable=False),
        sa.Column("difficulty", sa.Integer(), nullable=False),
        sa.Column("importance", sa.Numeric(precision=8, scale=4), nullable=True),
        sa.Column("importance_version", sa.String(length=32), nullable=True),
        sa.Column("current_affairs_linkable", sa.Boolean(), nullable=False),
        sa.Column("pyq_mappable", sa.Boolean(), nullable=False),
        sa.Column("pyq_count", sa.Integer(), nullable=False),
        sa.Column("exam_stages", postgresql.ARRAY(sa.String(length=32)), nullable=False),
        sa.Column("tags", postgresql.ARRAY(sa.String(length=64)), nullable=False),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("domain_catalog_version", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("prelims_relevance >= 0 AND prelims_relevance <= 100", name="ck_concepts_prelims_relevance"),
        sa.CheckConstraint("mains_relevance >= 0 AND mains_relevance <= 100", name="ck_concepts_mains_relevance"),
        sa.CheckConstraint("difficulty >= 1 AND difficulty <= 5", name="ck_concepts_difficulty"),
        sa.ForeignKeyConstraint(["exam_id"], ["exams.exam_id"], name=op.f("fk_concepts_exam_id_exams"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parent_concept_id"], ["concepts.concept_id"], name=op.f("fk_concepts_parent_concept_id_concepts"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.subject_id"], name=op.f("fk_concepts_subject_id_subjects"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["topic_id"], ["topics.topic_id"], name=op.f("fk_concepts_topic_id_topics"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("concept_id", name=op.f("pk_concepts")),
    )
    op.create_index(op.f("ix_concepts_exam_id"), "concepts", ["exam_id"], unique=False)
    op.create_index(op.f("ix_concepts_parent_concept_id"), "concepts", ["parent_concept_id"], unique=False)
    op.create_index(op.f("ix_concepts_status"), "concepts", ["status"], unique=False)
    op.create_index(op.f("ix_concepts_subject_id"), "concepts", ["subject_id"], unique=False)
    op.create_index(op.f("ix_concepts_topic_id"), "concepts", ["topic_id"], unique=False)
    op.create_index("ix_concepts_concept_name_trgm", "concepts", ["concept_name"], unique=False)
    op.create_index("ix_concepts_exam_id_status", "concepts", ["exam_id", "status"], unique=False)
    op.create_index("ix_concepts_subject_id_status", "concepts", ["subject_id", "status"], unique=False)
    op.create_index("ix_concepts_topic_id_status", "concepts", ["topic_id", "status"], unique=False)

    op.create_table(
        "concept_relationships",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("exam_id", sa.String(length=64), nullable=False),
        sa.Column("source_id", sa.String(length=256), nullable=False),
        sa.Column("source_type", sa.String(length=32), nullable=False),
        sa.Column("target_id", sa.String(length=256), nullable=False),
        sa.Column("target_type", sa.String(length=32), nullable=False),
        sa.Column("relationship_type", sa.String(length=32), nullable=False),
        sa.Column("weight", sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["exam_id"], ["exams.exam_id"], name=op.f("fk_concept_relationships_exam_id_exams"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_concept_relationships")),
        sa.UniqueConstraint("exam_id", "source_id", "target_id", "relationship_type", name="uq_concept_relationships_edge"),
    )
    op.create_index(op.f("ix_concept_relationships_exam_id"), "concept_relationships", ["exam_id"], unique=False)
    op.create_index(op.f("ix_concept_relationships_source_id"), "concept_relationships", ["source_id"], unique=False)
    op.create_index(op.f("ix_concept_relationships_target_id"), "concept_relationships", ["target_id"], unique=False)
    op.create_index("ix_concept_relationships_source_type", "concept_relationships", ["source_id", "relationship_type"], unique=False)
    op.create_index("ix_concept_relationships_target_type", "concept_relationships", ["target_id", "relationship_type"], unique=False)


def downgrade() -> None:
    op.drop_table("concept_relationships")
    op.drop_table("concepts")
    op.drop_table("catalog_versions")
    op.drop_table("topics")
    op.drop_table("subjects")
    op.drop_table("exam_tracks")
    op.drop_table("exams")
