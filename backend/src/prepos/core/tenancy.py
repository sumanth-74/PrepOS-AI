from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from uuid import UUID


class RoleName(StrEnum):
    STUDENT = "student"
    FACULTY = "faculty"
    INSTITUTE_ADMIN = "institute_admin"
    SUPER_ADMIN = "super_admin"


@dataclass(frozen=True, slots=True)
class TenantContext:
    tenant_id: UUID
    user_id: UUID
    roles: frozenset[RoleName] = field(default_factory=frozenset)
    request_id: str | None = None
    correlation_id: str | None = None

    def has_role(self, role: RoleName) -> bool:
        return role in self.roles or RoleName.SUPER_ADMIN in self.roles

    def require_role(self, *roles: RoleName) -> None:
        if RoleName.SUPER_ADMIN in self.roles:
            return
        if not any(self.has_role(role) for role in roles):
            from prepos.core.exceptions import TenantAccessDeniedError

            raise TenantAccessDeniedError("Insufficient role for this operation.")

    def require_tenant(self, resource_tenant_id: UUID) -> None:
        if self.tenant_id != resource_tenant_id:
            from prepos.core.exceptions import TenantAccessDeniedError

            raise TenantAccessDeniedError("Cross-tenant access denied.")
