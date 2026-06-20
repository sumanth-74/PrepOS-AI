from __future__ import annotations

import asyncio
from uuid import UUID

from prepos.core.config import get_settings
from prepos.core.database import create_engine, dispose_engine
from prepos.core.logging import configure_logging
from prepos.infrastructure.db.repositories.knowledge_repository import SqlAlchemyKnowledgeRepository
from prepos.infrastructure.knowledge.embedding_provider import build_embedding_provider
from prepos.tasks.celery_app import celery_app


@celery_app.task(name="prepos.tasks.knowledge_tasks.embed_source_chunks")  # type: ignore[untyped-decorator]
def embed_source_chunks(source_id: str) -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    create_engine(settings)

    async def _run() -> None:
        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

        from prepos.application.knowledge.services import KnowledgeEmbeddingService
        from prepos.core.database import get_engine

        engine = get_engine()
        session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with session_factory() as session:
            try:
                service = KnowledgeEmbeddingService(
                    settings=settings,
                    repository=SqlAlchemyKnowledgeRepository(session),
                    embedding_provider=build_embedding_provider(settings),
                )
                await service.embed_pending_chunks(UUID(source_id))
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    try:
        asyncio.run(_run())
    finally:
        asyncio.run(dispose_engine())
