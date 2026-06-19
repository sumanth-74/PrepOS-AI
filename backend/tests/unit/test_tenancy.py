from __future__ import annotations

from uuid import uuid4

import pytest

from prepos.core.exceptions import TenantAccessDeniedError
from prepos.core.tenancy import RoleName, TenantContext


def test_tenant_context_role_check() -> None:
    ctx = TenantContext(
        tenant_id=uuid4(),
        user_id=uuid4(),
        roles=frozenset({RoleName.STUDENT}),
    )
    assert ctx.has_role(RoleName.STUDENT)
    assert not ctx.has_role(RoleName.FACULTY)


def test_super_admin_has_all_roles() -> None:
    ctx = TenantContext(
        tenant_id=uuid4(),
        user_id=uuid4(),
        roles=frozenset({RoleName.SUPER_ADMIN}),
    )
    assert ctx.has_role(RoleName.FACULTY)


def test_require_tenant_blocks_cross_tenant() -> None:
    tenant_a = uuid4()
    tenant_b = uuid4()
    ctx = TenantContext(tenant_id=tenant_a, user_id=uuid4(), roles=frozenset({RoleName.STUDENT}))
    with pytest.raises(TenantAccessDeniedError):
        ctx.require_tenant(tenant_b)
