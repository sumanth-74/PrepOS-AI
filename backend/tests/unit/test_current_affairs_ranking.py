from __future__ import annotations

from datetime import UTC, datetime, timedelta

from prepos.domain.knowledge.current_affairs import (
    apply_ranking_boosts,
    authority_boost_multiplier,
    is_current_affairs_source_type,
    recency_boost_multiplier,
)


def test_recency_boost_prefers_newer_articles() -> None:
    now = datetime(2026, 6, 18, tzinfo=UTC)
    recent = recency_boost_multiplier(now - timedelta(days=2), reference_time=now)
    older = recency_boost_multiplier(now - timedelta(days=120), reference_time=now)
    assert recent > older


def test_authority_boost_multiplier_for_pib() -> None:
    assert authority_boost_multiplier("pib", None) == 1.25


def test_apply_ranking_boosts_increases_score_for_recent_pib() -> None:
    now = datetime(2026, 6, 18, tzinfo=UTC)
    boosted = apply_ranking_boosts(
        base_score=1.0,
        published_at=now - timedelta(days=1),
        source_authority="pib",
        source_type="pib",
        prefer_recency=True,
        reference_time=now,
    )
    plain = apply_ranking_boosts(
        base_score=1.0,
        published_at=now - timedelta(days=365),
        source_authority=None,
        source_type="upload",
        prefer_recency=False,
        reference_time=now,
    )
    assert boosted > plain


def test_current_affairs_source_types() -> None:
    assert is_current_affairs_source_type("pib")
    assert not is_current_affairs_source_type("ncert")
