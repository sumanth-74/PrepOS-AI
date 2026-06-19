from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from prepos.application.auth.ports import (
    AuditLogRepositoryPort,
    RefreshTokenRepositoryPort,
    TenantRepositoryPort,
    UserRepositoryPort,
)
from prepos.core.exceptions import NotFoundError
from prepos.core.tenancy import RoleName
from prepos.domain.auth.entities import Tenant, User
from prepos.infrastructure.db.models.foundation import (
    AuditLogModel,
    RefreshTokenModel,
    RoleModel,
    RolePermissionModel,
    TenantModel,
    UserModel,
    UserRoleModel,
)


def _map_tenant(row: TenantModel) -> Tenant:
    return Tenant(
        id=row.id,
        name=row.name,
        slug=row.slug,
        is_active=row.is_active,
        timezone=row.timezone,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _map_user(row: UserModel) -> User:
    roles = tuple(ur.role.name for ur in row.user_roles if ur.role is not None)
    permissions: set[str] = set()
    for ur in row.user_roles:
        if ur.role is None:
            continue
        for rp in ur.role.role_permissions:
            if rp.permission is not None:
                permissions.add(rp.permission.code)
    return User(
        id=row.id,
        tenant_id=row.tenant_id,
        email=row.email,
        full_name=row.full_name,
        is_active=row.is_active,
        roles=roles,
        permissions=tuple(sorted(permissions)),
        last_login_at=row.last_login_at,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class SqlAlchemyTenantRepository(TenantRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_slug(self, slug: str) -> Tenant | None:
        result = await self._session.execute(
            select(TenantModel).where(TenantModel.slug == slug)
        )
        row = result.scalar_one_or_none()
        return _map_tenant(row) if row else None

    async def get_by_id(self, tenant_id: UUID) -> Tenant | None:
        result = await self._session.execute(
            select(TenantModel).where(TenantModel.id == tenant_id)
        )
        row = result.scalar_one_or_none()
        return _map_tenant(row) if row else None

    async def create(self, *, name: str, slug: str, timezone: str) -> Tenant:
        row = TenantModel(name=name, slug=slug, timezone=timezone, is_active=True)
        self._session.add(row)
        await self._session.flush()
        await self._seed_roles()
        return _map_tenant(row)

    async def _seed_roles(self) -> None:
        existing = await self._session.execute(select(RoleModel.name))
        existing_names = set(existing.scalars().all())
        defaults = [
            (RoleName.STUDENT.value, "Student role"),
            (RoleName.FACULTY.value, "Faculty role"),
            (RoleName.INSTITUTE_ADMIN.value, "Institute administrator"),
            (RoleName.SUPER_ADMIN.value, "Platform super administrator"),
        ]
        for name, description in defaults:
            if name not in existing_names:
                self._session.add(RoleModel(name=name, description=description))
        await self._session.flush()


class SqlAlchemyUserRepository(UserRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def _load_user(self, tenant_id: UUID, user_id: UUID) -> UserModel | None:
        result = await self._session.execute(
            select(UserModel)
            .where(UserModel.tenant_id == tenant_id, UserModel.id == user_id)
            .options(
                selectinload(UserModel.user_roles)
                .selectinload(UserRoleModel.role)
                .selectinload(RoleModel.role_permissions)
                .selectinload(RolePermissionModel.permission)
            )
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, tenant_id: UUID, email: str) -> User | None:
        result = await self._session.execute(
            select(UserModel)
            .where(UserModel.tenant_id == tenant_id, UserModel.email == email)
            .options(
                selectinload(UserModel.user_roles)
                .selectinload(UserRoleModel.role)
                .selectinload(RoleModel.role_permissions)
                .selectinload(RolePermissionModel.permission)
            )
        )
        row = result.scalar_one_or_none()
        return _map_user(row) if row else None

    async def get_by_id(self, tenant_id: UUID, user_id: UUID) -> User | None:
        row = await self._load_user(tenant_id, user_id)
        return _map_user(row) if row else None

    async def get_with_password_hash(
        self, tenant_id: UUID, user_id: UUID
    ) -> tuple[User, str] | None:
        result = await self._session.execute(
            select(UserModel)
            .where(UserModel.tenant_id == tenant_id, UserModel.id == user_id)
            .options(
                selectinload(UserModel.user_roles)
                .selectinload(UserRoleModel.role)
                .selectinload(RoleModel.role_permissions)
                .selectinload(RolePermissionModel.permission)
            )
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return _map_user(row), row.password_hash

    async def create(
        self,
        *,
        tenant_id: UUID,
        email: str,
        password_hash: str,
        full_name: str,
        role_names: list[str],
    ) -> User:
        user = UserModel(
            tenant_id=tenant_id,
            email=email,
            password_hash=password_hash,
            full_name=full_name,
            is_active=True,
        )
        self._session.add(user)
        await self._session.flush()

        roles_result = await self._session.execute(
            select(RoleModel).where(RoleModel.name.in_(role_names))
        )
        roles = list(roles_result.scalars().all())
        if len(roles) != len(role_names):
            raise NotFoundError("One or more roles not found.")

        for role in roles:
            self._session.add(
                UserRoleModel(tenant_id=tenant_id, user_id=user.id, role_id=role.id)
            )
        await self._session.flush()
        loaded = await self._load_user(tenant_id, user.id)
        assert loaded is not None
        return _map_user(loaded)

    async def update_last_login(self, tenant_id: UUID, user_id: UUID) -> None:
        row = await self._load_user(tenant_id, user_id)
        if row is None:
            return
        row.last_login_at = datetime.now(UTC)
        await self._session.flush()


class SqlAlchemyRefreshTokenRepository(RefreshTokenRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def store(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        token_jti: str,
        expires_at: object,
    ) -> None:
        assert isinstance(expires_at, datetime)
        self._session.add(
            RefreshTokenModel(
                tenant_id=tenant_id,
                user_id=user_id,
                token_jti=token_jti,
                expires_at=expires_at,
            )
        )
        await self._session.flush()

    async def revoke_by_jti(self, token_jti: str) -> None:
        result = await self._session.execute(
            select(RefreshTokenModel).where(RefreshTokenModel.token_jti == token_jti)
        )
        row = result.scalar_one_or_none()
        if row and row.revoked_at is None:
            row.revoked_at = datetime.now(UTC)
            await self._session.flush()

    async def is_revoked(self, token_jti: str) -> bool:
        result = await self._session.execute(
            select(RefreshTokenModel).where(RefreshTokenModel.token_jti == token_jti)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return True
        return row.revoked_at is not None

    async def revoke_all_for_user(self, tenant_id: UUID, user_id: UUID) -> None:
        result = await self._session.execute(
            select(RefreshTokenModel).where(
                RefreshTokenModel.tenant_id == tenant_id,
                RefreshTokenModel.user_id == user_id,
                RefreshTokenModel.revoked_at.is_(None),
            )
        )
        now = datetime.now(UTC)
        for row in result.scalars().all():
            row.revoked_at = now
        await self._session.flush()


class SqlAlchemyAuditLogRepository(AuditLogRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

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
    ) -> None:
        self._session.add(
            AuditLogModel(
                id=uuid4(),
                tenant_id=tenant_id,
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                correlation_id=correlation_id,
                metadata_json=metadata or {},
                created_at=datetime.now(UTC),
            )
        )
        await self._session.flush()
