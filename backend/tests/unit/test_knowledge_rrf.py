from __future__ import annotations

from uuid import UUID, uuid4

from prepos.domain.knowledge.rrf import reciprocal_rank_fusion


def test_reciprocal_rank_fusion_merges_lists() -> None:
    first = uuid4()
    second = uuid4()
    third = uuid4()

    fused = reciprocal_rank_fusion(
        [
            [(first, 0.9), (second, 0.8)],
            [(second, 0.95), (third, 0.7)],
        ],
        k=60,
    )
    ids = [chunk_id for chunk_id, _, _, _ in fused]
    assert ids[0] == second
    assert set(ids) == {first, second, third}


def test_reciprocal_rank_fusion_empty() -> None:
    assert reciprocal_rank_fusion([]) == []
