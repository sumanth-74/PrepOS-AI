from __future__ import annotations

from collections import defaultdict
from uuid import UUID


def reciprocal_rank_fusion(
    ranked_lists: list[list[tuple[UUID, float]]],
    *,
    k: int = 60,
) -> list[tuple[UUID, float, float, float]]:
    """Merge ranked retrieval lists with Reciprocal Rank Fusion.

    Returns (chunk_id, fused_score, vector_component, keyword_component).
    Component scores are normalized RRF contributions per list (0 when absent).
    """
    if not ranked_lists:
        return []

    contributions: dict[UUID, list[float]] = defaultdict(lambda: [0.0] * len(ranked_lists))
    for list_index, ranked in enumerate(ranked_lists):
        for rank, (chunk_id, _raw_score) in enumerate(ranked, start=1):
            contributions[chunk_id][list_index] = 1.0 / (k + rank)

    fused: list[tuple[UUID, float, float, float]] = []
    for chunk_id, parts in contributions.items():
        vector_part = parts[0] if len(parts) > 0 else 0.0
        keyword_part = parts[1] if len(parts) > 1 else 0.0
        fused.append((chunk_id, sum(parts), vector_part, keyword_part))

    fused.sort(key=lambda item: item[1], reverse=True)
    return fused
