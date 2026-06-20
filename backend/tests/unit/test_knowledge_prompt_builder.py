from __future__ import annotations

from uuid import uuid4

from prepos.application.knowledge.prompt_builder import build_grounded_prompt
from prepos.application.knowledge.dto import KnowledgeSearchChunk, KnowledgeSourceSummary


def test_build_grounded_prompt_includes_student_context() -> None:
    chunk_id = uuid4()
    chunks = [
        KnowledgeSearchChunk(
            chunk_id=chunk_id,
            content="Federalism content",
            score=0.9,
            vector_score=0.9,
            keyword_score=0.8,
            source=KnowledgeSourceSummary(
                source_id=uuid4(),
                title="Polity Notes",
                source_type="ncert",
            ),
            metadata={},
        )
    ]

    _, user_prompt = build_grounded_prompt(
        query="Explain federalism",
        chunks=chunks,
        student_context="Student ID: abc\nWeakest concepts: polity_federalism",
    )

    assert "Student coaching context:" in user_prompt
    assert "polity_federalism" in user_prompt
    assert "Federalism content" in user_prompt
