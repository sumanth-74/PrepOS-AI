from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TextChunk:
    chunk_index: int
    content: str
    token_count: int


def estimate_token_count(text: str) -> int:
    """Approximate tokens as words * 1.3 — sufficient for chunk sizing without tiktoken."""
    words = len(text.split())
    return max(1, int(words * 1.3))


def chunk_text(
    text: str,
    *,
    chunk_size_tokens: int,
    overlap_tokens: int,
) -> list[TextChunk]:
    normalized = " ".join(text.split())
    if not normalized:
        return []

    words = normalized.split()
    if not words:
        return []

    approx_words_per_chunk = max(1, int(chunk_size_tokens / 1.3))
    overlap_words = max(0, int(overlap_tokens / 1.3))
    step = max(1, approx_words_per_chunk - overlap_words)

    chunks: list[TextChunk] = []
    start = 0
    chunk_index = 0
    while start < len(words):
        end = min(len(words), start + approx_words_per_chunk)
        content = " ".join(words[start:end]).strip()
        if content:
            chunks.append(
                TextChunk(
                    chunk_index=chunk_index,
                    content=content,
                    token_count=estimate_token_count(content),
                )
            )
            chunk_index += 1
        if end >= len(words):
            break
        start += step

    return chunks
