from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from prepos.domain.auth.entities import Tenant, User


class TenantRepositoryPort(ABC):
    @abstractmethod
    async def get_by_slug(self, slug: str) -> Tenant | None: ...

    @abstractmethod
    async def get_by_id(self, tenant_id: UUID) -> Tenant | None: ...

    @abstractmethod
    async def create(self, *, name: str, slug: str, timezone: str) -> Tenant: ...


class UserRepositoryPort(ABC):
    @abstractmethod
    async def get_by_email(self, tenant_id: UUID, email: str) -> User | None: ...

    @abstractmethod
    async def get_by_id(self, tenant_id: UUID, user_id: UUID) -> User | None: ...

    @abstractmethod
    async def get_with_password_hash(
        self, tenant_id: UUID, user_id: UUID
    ) -> tuple[User, str] | None: ...

    @abstractmethod
    async def create(
        self,
        *,
        tenant_id: UUID,
        email: str,
        password_hash: str,
        full_name: str,
        role_names: list[str],
    ) -> User: ...

    @abstractmethod
    async def update_last_login(self, tenant_id: UUID, user_id: UUID) -> None: ...


class RefreshTokenRepositoryPort(ABC):
    @abstractmethod
    async def store(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        token_jti: str,
        expires_at: object,
    ) -> None: ...

    @abstractmethod
    async def revoke_by_jti(self, token_jti: str) -> None: ...

    @abstractmethod
    async def is_revoked(self, token_jti: str) -> bool: ...

    @abstractmethod
    async def revoke_all_for_user(self, tenant_id: UUID, user_id: UUID) -> None: ...


class AuditLogRepositoryPort(ABC):
    @abstractmethod
    async def append(
        self,
        *,
        tenant_id: UUID | None,
        user_id: UUID | None,
        action: str,
        resource_type: str,
        resource_id: str | None,
        correlation_id: str | None,
        metadata: dict[str, object] | None = None,
    ) -> None: ...
