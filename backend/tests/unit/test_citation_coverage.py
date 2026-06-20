from __future__ import annotations

from uuid import uuid4

from prepos.domain.knowledge.evaluation_metrics import citation_coverage_score


def test_citation_coverage_full_when_all_statements_cited() -> None:
    chunk_id = uuid4()
    answer = f"Federalism divides powers between centre and states. [{chunk_id}]"
    score = citation_coverage_score(answer=answer, citation_count=1)
    assert score == 100.0


def test_citation_coverage_zero_when_no_citations() -> None:
    answer = "Federalism divides powers between centre and states without any citation."
    score = citation_coverage_score(answer=answer, citation_count=0)
    assert score == 0.0
