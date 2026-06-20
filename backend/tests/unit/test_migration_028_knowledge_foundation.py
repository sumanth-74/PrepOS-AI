"""Migration 028 knowledge foundation."""

from prepos.infrastructure.db.models.knowledge import (
    KnowledgeChunkEmbeddingModel,
    KnowledgeChunkModel,
    KnowledgeSourceModel,
)


def test_knowledge_source_model_has_observability_columns() -> None:
    columns = {column.name for column in KnowledgeSourceModel.__table__.columns}
    assert "embedding_failure_count" in columns
    assert "ingestion_failure_count" in columns
    assert "indexed_chunk_count" in columns


def test_knowledge_chunk_model_has_metadata_and_fts() -> None:
    columns = {column.name for column in KnowledgeChunkModel.__table__.columns}
    assert "metadata_json" in columns
    assert "content_tsv" in columns


def test_knowledge_chunk_embedding_model_has_vector_column() -> None:
    columns = {column.name for column in KnowledgeChunkEmbeddingModel.__table__.columns}
    assert "embedding" in columns
    assert "embedding_model" in columns
