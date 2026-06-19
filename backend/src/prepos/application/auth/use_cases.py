from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from jose import jwt

from prepos.application.auth.dto import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from prepos.application.auth.ports import (
    AuditLogRepositoryPort,
    RefreshTokenRepositoryPort,
    TenantRepositoryPort,
    UserRepositoryPort,
)
from prepos.core.config import Settings
from prepos.core.exceptions import AuthenticationError, ConflictError, NotFoundError
from prepos.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from prepos.core.tenancy import RoleName
from prepos.domain.auth.entities import User
from prepos.events.outbox.publisher import OutboxPublisher


class RegisterUseCase:
    def __init__(
        self,
        *,
        settings: Settings,
        tenant_repo: TenantRepositoryPort,
        user_repo: UserRepositoryPort,
        refresh_repo: RefreshTokenRepositoryPort,
        audit_repo: AuditLogRepositoryPort,
        outbox: OutboxPublisher,
    ) -> None:
        self._settings = settings
        self._tenant_repo = tenant_repo
        self._user_repo = user_repo
        self._refresh_repo = refresh_repo
        self._audit_repo = audit_repo
        self._outbox = outbox

    async def execute(self, request: RegisterRequest, correlation_id: str) -> TokenResponse:
        existing = await self._tenant_repo.get_by_slug(request.tenant_slug)
        if existing is not None:
            raise ConflictError("Tenant slug already exists.")

        tenant = await self._tenant_repo.create(
            name=request.tenant_name,
            slug=request.tenant_slug,
            timezone="Asia/Kolkata",
        )
        user = await self._user_repo.create(
            tenant_id=tenant.id,
            email=request.email.lower(),
            password_hash=hash_password(request.password),
            full_name=request.full_name,
            role_names=[RoleName.INSTITUTE_ADMIN.value],
        )

        await self._audit_repo.append(
            tenant_id=tenant.id,
            user_id=user.id,
            action="tenant.registered",
            resource_type="tenant",
            resource_id=str(tenant.id),
            correlation_id=correlation_id,
            metadata={"email": user.email},
        )

        await self._outbox.enqueue_student_registered(
            tenant_id=tenant.id,
            user_id=user.id,
            correlation_id=correlation_id,
        )

        return await _issue_tokens(
            settings=self._settings,
            refresh_repo=self._refresh_repo,
            user=user,
            store_refresh=True,
        )


class LoginUseCase:
    def __init__(
        self,
        *,
        settings: Settings,
        tenant_repo: TenantRepositoryPort,
        user_repo: UserRepositoryPort,
        refresh_repo: RefreshTokenRepositoryPort,
        audit_repo: AuditLogRepositoryPort,
    ) -> None:
        self._settings = settings
        self._tenant_repo = tenant_repo
        self._user_repo = user_repo
        self._refresh_repo = refresh_repo
        self._audit_repo = audit_repo

    async def execute(self, request: LoginRequest, correlation_id: str) -> TokenResponse:
        tenant = await self._tenant_repo.get_by_slug(request.tenant_slug)
        if tenant is None or not tenant.is_active:
            raise AuthenticationError("Invalid credentials.")

        user = await self._user_repo.get_by_email(tenant.id, request.email.lower())
        if user is None or not user.is_active:
            raise AuthenticationError("Invalid credentials.")

        stored = await self._user_repo.get_with_password_hash(tenant.id, user.id)
        if stored is None or not verify_password(request.password, stored[1]):
            raise AuthenticationError("Invalid credentials.")

        await self._user_repo.update_last_login(tenant.id, user.id)
        await self._audit_repo.append(
            tenant_id=tenant.id,
            user_id=user.id,
            action="auth.login",
            resource_type="user",
            resource_id=str(user.id),
            correlation_id=correlation_id,
        )

        refreshed_user = await self._user_repo.get_by_id(tenant.id, user.id)
        assert refreshed_user is not None
        return await _issue_tokens(
            settings=self._settings,
            refresh_repo=self._refresh_repo,
            user=refreshed_user,
            store_refresh=True,
        )


class RefreshTokenUseCase:
    def __init__(
        self,
        *,
        settings: Settings,
        user_repo: UserRepositoryPort,
        refresh_repo: RefreshTokenRepositoryPort,
    ) -> None:
        self._settings = settings
        self._user_repo = user_repo
        self._refresh_repo = refresh_repo

    async def execute(self, request: RefreshRequest) -> TokenResponse:
        payload = decode_token(self._settings, request.refresh_token)
        if payload.get("type") != "refresh":
            raise AuthenticationError("Invalid refresh token.")

        jti = str(payload.get("jti", ""))
        if not jti or await self._refresh_repo.is_revoked(jti):
            raise AuthenticationError("Refresh token revoked.")

        tenant_id = UUID(str(payload["tenant_id"]))
        user_id = UUID(str(payload["sub"]))
        user = await self._user_repo.get_by_id(tenant_id, user_id)
        if user is None or not user.is_active:
            raise AuthenticationError("User not found.")

        await self._refresh_repo.revoke_by_jti(jti)
        return await _issue_tokens(
            settings=self._settings,
            refresh_repo=self._refresh_repo,
            user=user,
            store_refresh=True,
        )


class LogoutUseCase:
    def __init__(
        self,
        *,
        settings: Settings,
        refresh_repo: RefreshTokenRepositoryPort,
        audit_repo: AuditLogRepositoryPort,
    ) -> None:
        self._settings = settings
        self._refresh_repo = refresh_repo
        self._audit_repo = audit_repo

    async def execute(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        refresh_token: str | None,
        correlation_id: str,
    ) -> None:
        if refresh_token:
            payload = decode_token(self._settings, refresh_token)
            jti = str(payload.get("jti", ""))
            if jti:
                await self._refresh_repo.revoke_by_jti(jti)
        await self._refresh_repo.revoke_all_for_user(tenant_id, user_id)
        await self._audit_repo.append(
            tenant_id=tenant_id,
            user_id=user_id,
            action="auth.logout",
            resource_type="user",
            resource_id=str(user_id),
            correlation_id=correlation_id,
        )


class GetCurrentUserUseCase:
    def __init__(self, *, user_repo: UserRepositoryPort) -> None:
        self._user_repo = user_repo

    async def execute(self, tenant_id: UUID, user_id: UUID) -> UserResponse:
        user = await self._user_repo.get_by_id(tenant_id, user_id)
        if user is None:
            raise NotFoundError("User not found.")
        return UserResponse(
            id=str(user.id),
            tenant_id=str(user.tenant_id),
            email=user.email,
            full_name=user.full_name,
            roles=list(user.roles),
            permissions=list(user.permissions),
        )


async def _issue_tokens(
    *,
    settings: Settings,
    refresh_repo: RefreshTokenRepositoryPort,
    user: User,
    store_refresh: bool,
) -> TokenResponse:
    session_id = uuid4()
    access = create_access_token(
        settings=settings,
        user_id=user.id,
        tenant_id=user.tenant_id,
        roles=list(user.roles),
        session_id=session_id,
    )
    refresh = create_refresh_token(
        settings=settings,
        user_id=user.id,
        tenant_id=user.tenant_id,
        session_id=session_id,
    )
    if store_refresh:
        refresh_payload = jwt.get_unverified_claims(refresh)
        expires_at = datetime.fromtimestamp(float(refresh_payload["exp"]), tz=UTC)
        await refresh_repo.store(
            tenant_id=user.tenant_id,
            user_id=user.id,
            token_jti=str(refresh_payload["jti"]),
            expires_at=expires_at,
        )
    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        expires_in=settings.access_token_expire_minutes * 60,
    )
