"""Role-Based Access Control (RBAC) dependencies and permission guard evaluators for Phase 10."""

from typing import Callable, List, Union
from fastapi import Depends, HTTPException, status

from aurix_api.schemas.auth import Permission, Role, TenantContext
from aurix_api.security.auth import get_current_tenant_context


class PermissionChecker:
    """FastAPI dependency verifying that the authenticated user possesses the required permission."""

    def __init__(self, required_permission: Permission) -> None:
        self.required_permission = required_permission

    def __call__(
        self,
        tenant_context: TenantContext = Depends(get_current_tenant_context),
    ) -> TenantContext:
        """Evaluates permission against tenant context, raising 403 Forbidden on failure."""
        if not tenant_context.has_permission(self.required_permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Access forbidden: User '{tenant_context.user.user_id}' in tenant '{tenant_context.tenant_id}' "
                    f"lacks the required '{self.required_permission.value}' permission."
                ),
            )
        return tenant_context


class RoleChecker:
    """FastAPI dependency verifying that the authenticated user possesses at least one authorized role."""

    def __init__(self, allowed_roles: List[Role]) -> None:
        self.allowed_roles = allowed_roles

    def __call__(
        self,
        tenant_context: TenantContext = Depends(get_current_tenant_context),
    ) -> TenantContext:
        """Evaluates user roles against authorized role list, raising 403 Forbidden on failure."""
        user_roles = set(tenant_context.user.roles)
        # ADMIN role always bypasses role checks
        if Role.ADMIN in user_roles:
            return tenant_context

        if not any(role in user_roles for role in self.allowed_roles):
            role_names = ", ".join(r.value for r in self.allowed_roles)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Access forbidden: User '{tenant_context.user.user_id}' does not have any of the authorized "
                    f"roles: [{role_names}]."
                ),
            )
        return tenant_context


def require_permission(permission: Permission) -> Callable[[TenantContext], TenantContext]:
    """Dependency helper requiring a specific operational permission."""
    return PermissionChecker(permission)


def require_roles(roles: Union[Role, List[Role]]) -> Callable[[TenantContext], TenantContext]:
    """Dependency helper requiring at least one of the specified roles."""
    role_list = [roles] if isinstance(roles, Role) else roles
    return RoleChecker(role_list)