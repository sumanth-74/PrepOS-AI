from __future__ import annotations

import asyncio
from pathlib import Path
from uuid import UUID

from prepos.application.knowledge.ports import KnowledgeStoragePort
from prepos.core.config import Settings


class LocalKnowledgeStorage(KnowledgeStoragePort):
    def __init__(self, settings: Settings) -> None:
        self._root = Path(settings.knowledge_storage_path)

    async def save_upload(
        self,
        *,
        tenant_id: UUID | None,
        source_id: UUID,
        file_name: str,
        content: bytes,
    ) -> str:
        tenant_segment = str(tenant_id) if tenant_id else "platform"
        target_dir = self._root / tenant_segment / str(source_id)
        target_path = target_dir / Path(file_name).name

        def _write() -> str:
            target_dir.mkdir(parents=True, exist_ok=True)
            target_path.write_bytes(content)
            return str(target_path)

        return await asyncio.to_thread(_write)

    async def read_text(self, external_uri: str) -> str:
        return await asyncio.to_thread(Path(external_uri).read_text, encoding="utf-8")
