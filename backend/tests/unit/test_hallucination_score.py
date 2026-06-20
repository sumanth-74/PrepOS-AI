from __future__ import annotations

from prepos.domain.knowledge.evaluation_metrics import hallucination_score


def test_hallucination_score_low_for_supported_cited_answer() -> None:
    score = hallucination_score(
        answer="Federalism divides powers between centre and states.",
        citation_coverage=100.0,
        support_score_value=85.0,
        citation_count=1,
    )
    assert score <= 20.0


def test_hallucination_score_high_for_uncited_unsupported_answer() -> None:
    score = hallucination_score(
        answer="Quantum entanglement governs constitutional amendments in India.",
        citation_coverage=0.0,
        support_score_value=5.0,
        citation_count=0,
    )
    assert score >= 60.0


def test_hallucination_score_zero_for_insufficient_evidence_answer() -> None:
    score = hallucination_score(
        answer="I don't have enough indexed content to answer confidently.",
        citation_coverage=0.0,
        support_score_value=0.0,
        citation_count=0,
    )
    assert score == 0.0
