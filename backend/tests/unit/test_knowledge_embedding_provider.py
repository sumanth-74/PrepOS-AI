from __future__ import annotations

import pytest

from prepos.infrastructure.knowledge.embedding_provider import (
    DeterministicEmbeddingProvider,
    OpenAIEmbeddingProvider,
)
from prepos.core.config import Settings
from prepos.core.exceptions import ValidationError


@pytest.mark.asyncio
async def test_deterministic_embedding_is_normalized() -> None:
    provider = DeterministicEmbeddingProvider(dimensions=16)
    vectors = await provider.embed_texts(["alpha", "beta"])
    assert len(vectors) == 2
    assert len(vectors[0]) == 16
    norm = sum(value * value for value in vectors[0]) ** 0.5
    assert abs(norm - 1.0) < 0.01


@pytest.mark.asyncio
async def test_deterministic_embedding_is_stable() -> None:
    provider = DeterministicEmbeddingProvider(dimensions=32)
    first = await provider.embed_texts(["same text"])
    second = await provider.embed_texts(["same text"])
    assert first[0] == second[0]


def test_openai_provider_requires_api_key() -> None:
    settings = Settings(
        secret_key="test-secret-key-for-prepos-backend-foundation-32chars-min",
        database_url="postgresql+asyncpg://prepos:prepos@localhost:5432/prepos",
        openai_api_key=None,
    )
    with pytest.raises(ValidationError):
        OpenAIEmbeddingProvider(settings)
