from __future__ import annotations

from prepos.domain.knowledge.chunking import chunk_text, estimate_token_count


def test_estimate_token_count_non_empty() -> None:
    assert estimate_token_count("one two three four") >= 4


def test_chunk_text_splits_long_content() -> None:
    words = " ".join(f"word{i}" for i in range(500))
    chunks = chunk_text(words, chunk_size_tokens=100, overlap_tokens=20)
    assert len(chunks) > 1
    assert chunks[0].chunk_index == 0
    assert all(chunk.content for chunk in chunks)


def test_chunk_text_empty_input() -> None:
    assert chunk_text("", chunk_size_tokens=100, overlap_tokens=20) == []
    assert chunk_text("   ", chunk_size_tokens=100, overlap_tokens=20) == []
