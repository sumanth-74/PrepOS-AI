from __future__ import annotations

import hashlib
import math

import httpx
import structlog

from prepos.application.knowledge.ports import EmbeddingProviderPort
from prepos.core.config import Settings
from prepos.core.exceptions import ValidationError

logger = structlog.get_logger(__name__)


class OpenAIEmbeddingProvider(EmbeddingProviderPort):
    def __init__(self, settings: Settings) -> None:
        if not settings.openai_api_key:
            raise ValidationError("OPENAI_API_KEY is required for embedding generation.")
        self._settings = settings
        self._api_key = settings.openai_api_key

    @property
    def model_name(self) -> str:
        return self._settings.embedding_model

    @property
    def dimensions(self) -> int:
        return self._settings.embedding_dims

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/embeddings",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model_name,
                    "input": texts,
                    "dimensions": self.dimensions,
                },
            )
            response.raise_for_status()
            payload = response.json()

        data = payload.get("data", [])
        if not isinstance(data, list) or len(data) != len(texts):
            raise ValidationError("Unexpected embedding response from OpenAI.")

        vectors: list[list[float]] = [[] for _ in texts]
        for item in data:
            if not isinstance(item, dict):
                continue
            index = int(item.get("index", 0))
            embedding = item.get("embedding")
            if isinstance(embedding, list):
                vectors[index] = [float(value) for value in embedding]

        if any(not vector for vector in vectors):
            raise ValidationError("Incomplete embedding response from OpenAI.")
        return vectors


class DeterministicEmbeddingProvider(EmbeddingProviderPort):
    """Deterministic embeddings for tests and local development without OpenAI."""

    def __init__(self, *, model_name: str = "deterministic-embedding", dimensions: int = 1536) -> None:
        self._model_name = model_name
        self._dimensions = dimensions

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def dimensions(self) -> int:
        return self._dimensions

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [_hash_to_vector(text, self._dimensions) for text in texts]


def build_embedding_provider(settings: Settings) -> EmbeddingProviderPort:
    if settings.openai_api_key:
        return OpenAIEmbeddingProvider(settings)
    logger.warning("openai_api_key_missing_using_deterministic_embeddings")
    return DeterministicEmbeddingProvider(
        model_name=settings.embedding_model,
        dimensions=settings.embedding_dims,
    )


def _hash_to_vector(text: str, dimensions: int) -> list[float]:
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    values: list[float] = []
    seed = int.from_bytes(digest[:8], "big")
    for index in range(dimensions):
        seed = (seed * 1_103_515_245 + 12_345 + index) & 0xFFFFFFFFFFFFFFFF
        unit = ((seed % 10_000) / 10_000.0) * 2.0 - 1.0
        values.append(unit)
    norm = math.sqrt(sum(value * value for value in values)) or 1.0
    return [value / norm for value in values]
