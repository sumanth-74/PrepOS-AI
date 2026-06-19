from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    ARRAY,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from prepos.infrastructure.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ExamModel(Base, TimestampMixin):
    __tablename__ = "exams"

    exam_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    exam_code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    exam_name: Mapped[str] = mapped_column(String(512), nullable=False)
    exam_type: Mapped[str] = mapped_column(String(64), nullable=False)
    prelims_weight: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    mains_weight: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    interview_weight: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    domain_catalog_version: Mapped[str] = mapped_column(String(32), nullable=False, default="1.0.0")
    essay_included: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active", index=True)

    tracks: Mapped[list[ExamTrackModel]] = relationship(back_populates="exam", cascade="all, delete-orphan")
    subjects: Mapped[list[SubjectModel]] = relationship(back_populates="exam", cascade="all, delete-orphan")
    catalog_versions: Mapped[list[CatalogVersionModel]] = relationship(
        back_populates="exam",
        cascade="all, delete-orphan",
    )


class ExamTrackModel(Base, TimestampMixin):
    __tablename__ = "exam_tracks"
    __table_args__ = (
        UniqueConstraint("exam_id", "track_code", name="uq_exam_tracks_exam_code"),
        Index("ix_exam_tracks_exam_id_status", "exam_id", "status"),
    )

    track_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    exam_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("exams.exam_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    track_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    track_name: Mapped[str] = mapped_column(String(255), nullable=False)
    stage: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    subject_ids: Mapped[list[str]] = mapped_column(ARRAY(String(128)), nullable=False, default=list)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")

    exam: Mapped[ExamModel] = relationship(back_populates="tracks")


class SubjectModel(Base, TimestampMixin):
    __tablename__ = "subjects"
    __table_args__ = (
        Index("ix_subjects_exam_id_status", "exam_id", "status"),
        Index("ix_subjects_exam_id_sort_order", "exam_id", "sort_order"),
    )

    subject_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    exam_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("exams.exam_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    subject_name: Mapped[str] = mapped_column(String(255), nullable=False)
    subject_slug: Mapped[str] = mapped_column(String(128), nullable=False)
    prelims_applicable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    mains_applicable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active", index=True)

    exam: Mapped[ExamModel] = relationship(back_populates="subjects")
    topics: Mapped[list[TopicModel]] = relationship(back_populates="subject", cascade="all, delete-orphan")


class TopicModel(Base, TimestampMixin):
    __tablename__ = "topics"
    __table_args__ = (
        Index("ix_topics_subject_id_status", "subject_id", "status"),
        Index("ix_topics_exam_id_status", "exam_id", "status"),
        CheckConstraint("prelims_relevance >= 0 AND prelims_relevance <= 100", name="ck_topics_prelims_relevance"),
        CheckConstraint("mains_relevance >= 0 AND mains_relevance <= 100", name="ck_topics_mains_relevance"),
    )

    topic_id: Mapped[str] = mapped_column(String(192), primary_key=True)
    exam_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("exams.exam_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    subject_id: Mapped[str] = mapped_column(
        String(128),
        ForeignKey("subjects.subject_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    topic_name: Mapped[str] = mapped_column(String(255), nullable=False)
    topic_slug: Mapped[str] = mapped_column(String(128), nullable=False)
    prelims_relevance: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    mains_relevance: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active", index=True)

    subject: Mapped[SubjectModel] = relationship(back_populates="topics")
    concepts: Mapped[list[ConceptModel]] = relationship(back_populates="topic", cascade="all, delete-orphan")


class ConceptModel(Base, TimestampMixin):
    __tablename__ = "concepts"
    __table_args__ = (
        Index("ix_concepts_topic_id_status", "topic_id", "status"),
        Index("ix_concepts_subject_id_status", "subject_id", "status"),
        Index("ix_concepts_exam_id_status", "exam_id", "status"),
        Index("ix_concepts_concept_name_trgm", "concept_name"),
        CheckConstraint("prelims_relevance >= 0 AND prelims_relevance <= 100", name="ck_concepts_prelims_relevance"),
        CheckConstraint("mains_relevance >= 0 AND mains_relevance <= 100", name="ck_concepts_mains_relevance"),
        CheckConstraint("difficulty >= 1 AND difficulty <= 5", name="ck_concepts_difficulty"),
    )

    concept_id: Mapped[str] = mapped_column(String(256), primary_key=True)
    exam_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("exams.exam_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    subject_id: Mapped[str] = mapped_column(
        String(128),
        ForeignKey("subjects.subject_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    topic_id: Mapped[str] = mapped_column(
        String(192),
        ForeignKey("topics.topic_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    parent_concept_id: Mapped[str | None] = mapped_column(
        String(256),
        ForeignKey("concepts.concept_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    concept_name: Mapped[str] = mapped_column(String(512), nullable=False)
    concept_slug: Mapped[str] = mapped_column(String(128), nullable=False)
    concept_type: Mapped[str] = mapped_column(String(64), nullable=False)
    prelims_relevance: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    mains_relevance: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    interview_relevance: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    difficulty: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    importance: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    importance_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    current_affairs_linkable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    pyq_mappable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    pyq_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    exam_stages: Mapped[list[str]] = mapped_column(ARRAY(String(32)), nullable=False, default=list)
    tags: Mapped[list[str]] = mapped_column(ARRAY(String(64)), nullable=False, default=list)
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active", index=True)
    domain_catalog_version: Mapped[str] = mapped_column(String(32), nullable=False, default="1.0.0")

    topic: Mapped[TopicModel] = relationship(back_populates="concepts")
    parent: Mapped[ConceptModel | None] = relationship(
        remote_side="ConceptModel.concept_id",
        back_populates="children",
    )
    children: Mapped[list[ConceptModel]] = relationship(back_populates="parent")


class ConceptRelationshipModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "concept_relationships"
    __table_args__ = (
        Index("ix_concept_relationships_source_type", "source_id", "relationship_type"),
        Index("ix_concept_relationships_target_type", "target_id", "relationship_type"),
        UniqueConstraint(
            "exam_id",
            "source_id",
            "target_id",
            "relationship_type",
            name="uq_concept_relationships_edge",
        ),
    )

    exam_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("exams.exam_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_id: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    target_id: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    target_type: Mapped[str] = mapped_column(String(32), nullable=False, default="concept")
    relationship_type: Mapped[str] = mapped_column(String(32), nullable=False)
    weight: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False, default=Decimal("1.0"))
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")


class CatalogVersionModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "catalog_versions"
    __table_args__ = (
        UniqueConstraint("exam_id", "version", name="uq_catalog_versions_exam_version"),
        Index("ix_catalog_versions_exam_id_status", "exam_id", "status"),
    )

    exam_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("exams.exam_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft", index=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    published_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    concepts_added: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    concepts_deprecated: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    change_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    exam: Mapped[ExamModel] = relationship(back_populates="catalog_versions")
