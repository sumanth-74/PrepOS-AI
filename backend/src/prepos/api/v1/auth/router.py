from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from prepos.api.deps import (
    get_current_context,
    get_current_user_use_case,
    get_login_use_case,
    get_logout_use_case,
    get_refresh_use_case,
    get_register_use_case,
    get_request_id,
)
from prepos.application.auth.dto import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from prepos.application.auth.use_cases import (
    GetCurrentUserUseCase,
    LoginUseCase,
    LogoutUseCase,
    RefreshTokenUseCase,
    RegisterUseCase,
)
from prepos.core.config import Settings, get_settings
from prepos.core.tenancy import TenantContext

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_auth_cookies(response: Response, tokens: TokenResponse, settings: Settings) -> None:
    response.set_cookie(
        key="access_token",
        value=tokens.access_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=tokens.expires_in,
    )
    response.set_cookie(
        key="refresh_token",
        value=tokens.refresh_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=settings.refresh_token_expire_days * 86400,
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    body: RegisterRequest,
    response: Response,
    use_case: Annotated[RegisterUseCase, Depends(get_register_use_case)],
    settings: Annotated[Settings, Depends(get_settings)],
    request_id: Annotated[str, Depends(get_request_id)],
) -> TokenResponse:
    tokens = await use_case.execute(body, request_id)
    _set_auth_cookies(response, tokens, settings)
    return tokens


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    response: Response,
    use_case: Annotated[LoginUseCase, Depends(get_login_use_case)],
    settings: Annotated[Settings, Depends(get_settings)],
    request_id: Annotated[str, Depends(get_request_id)],
) -> TokenResponse:
    tokens = await use_case.execute(body, request_id)
    _set_auth_cookies(response, tokens, settings)
    return tokens


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    body: RefreshRequest,
    response: Response,
    use_case: Annotated[RefreshTokenUseCase, Depends(get_refresh_use_case)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> TokenResponse:
    tokens = await use_case.execute(body)
    _set_auth_cookies(response, tokens, settings)
    return tokens


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    ctx: Annotated[TenantContext, Depends(get_current_context)],
    use_case: Annotated[LogoutUseCase, Depends(get_logout_use_case)],
    settings: Annotated[Settings, Depends(get_settings)],
    refresh_body: RefreshRequest | None = None,
) -> Response:
    refresh_token = refresh_body.refresh_token if refresh_body else None
    await use_case.execute(
        tenant_id=ctx.tenant_id,
        user_id=ctx.user_id,
        refresh_token=refresh_token,
        correlation_id=ctx.correlation_id or ctx.request_id or "",
    )
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=UserResponse)
async def me(
    ctx: Annotated[TenantContext, Depends(get_current_context)],
    use_case: Annotated[GetCurrentUserUseCase, Depends(get_current_user_use_case)],
) -> UserResponse:
    return await use_case.execute(ctx.tenant_id, ctx.user_id)
