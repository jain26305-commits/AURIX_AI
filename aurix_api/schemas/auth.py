"""Authentication and Role-Based Access Control (RBAC) schemas for Phases 10–14."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class Role(str, Enum):
    """Platform security roles."""
    ADMIN = "ADMIN"
    OPERATOR = "OPERATOR"
    ANALYST = "ANALYST"
    VIEWER = "VIEWER"
    INTEGRATION = "INTEGRATION"
    EXECUTIVE = "EXECUTIVE"
    AI_AGENT = "AI_AGENT"


class Permission(str, Enum):
    """Granular operational permissions across the platform."""
    # Data & Analytics Permissions (Phase 10)
    READ_DATA = "READ_DATA"
    WRITE_DATA = "WRITE_DATA"
    RUN_ANALYSIS = "RUN_ANALYSIS"
    USE_AI = "USE_AI"
    VIEW_FINANCIALS = "VIEW_FINANCIALS"
    OVERRIDE_POLICIES = "OVERRIDE_POLICIES"
    EXPORT_REPORTS = "EXPORT_REPORTS"
    MANAGE_USERS = "MANAGE_USERS"
    MANAGE_TENANT = "MANAGE_TENANT"
    CONFIGURE_INTELLIGENCE = "CONFIGURE_INTELLIGENCE"

    # Universal Integration & Connectivity Permissions (Phase 12)
    MANAGE_CONNECTORS = "MANAGE_CONNECTORS"
    TRIGGER_SYNC = "TRIGGER_SYNC"
    VIEW_LINEAGE = "VIEW_LINEAGE"
    VIEW_RECONCILIATION = "VIEW_RECONCILIATION"

    # Real-Time & Event-Driven Intelligence Permissions (Phase 13)
    MANAGE_EVENTS = "MANAGE_EVENTS"
    VIEW_EVENTS = "VIEW_EVENTS"
    MANAGE_ALERTS = "MANAGE_ALERTS"

    # Controlled Decision Execution Permissions (Phase 14)
    APPROVE_ACTION = "APPROVE_ACTION"
    EXECUTE_ACTION = "EXECUTE_ACTION"
    CANCEL_ACTION = "CANCEL_ACTION"
    VIEW_ACTION = "VIEW_ACTION"
    VIEW_ACTION_AUDIT = "VIEW_ACTION_AUDIT"


# Default role-permission matrix
DEFAULT_ROLE_PERMISSIONS: Dict[Role, List[Permission]] = {
    Role.ADMIN: [
        Permission.READ_DATA,
        Permission.WRITE_DATA,
        Permission.RUN_ANALYSIS,
        Permission.USE_AI,
        Permission.VIEW_FINANCIALS,
        Permission.OVERRIDE_POLICIES,
        Permission.EXPORT_REPORTS,
        Permission.MANAGE_USERS,
        Permission.MANAGE_TENANT,
        Permission.CONFIGURE_INTELLIGENCE,
        Permission.MANAGE_CONNECTORS,
        Permission.TRIGGER_SYNC,
        Permission.VIEW_LINEAGE,
        Permission.VIEW_RECONCILIATION,
        Permission.MANAGE_EVENTS,
        Permission.VIEW_EVENTS,
        Permission.MANAGE_ALERTS,
        Permission.APPROVE_ACTION,
        Permission.EXECUTE_ACTION,
        Permission.CANCEL_ACTION,
        Permission.VIEW_ACTION,
        Permission.VIEW_ACTION_AUDIT,
    ],
    Role.INTEGRATION: [
        Permission.READ_DATA,
        Permission.WRITE_DATA,
        Permission.TRIGGER_SYNC,
        Permission.MANAGE_CONNECTORS,
        Permission.VIEW_LINEAGE,
        Permission.VIEW_RECONCILIATION,
        Permission.VIEW_EVENTS,
        Permission.VIEW_ACTION,
    ],
    Role.OPERATOR: [
        Permission.READ_DATA,
        Permission.WRITE_DATA,
        Permission.RUN_ANALYSIS,
        Permission.TRIGGER_SYNC,
        Permission.VIEW_RECONCILIATION,
        Permission.EXPORT_REPORTS,
        Permission.MANAGE_EVENTS,
        Permission.VIEW_EVENTS,
        Permission.MANAGE_ALERTS,
        Permission.APPROVE_ACTION,
        Permission.EXECUTE_ACTION,
        Permission.CANCEL_ACTION,
        Permission.VIEW_ACTION,
        Permission.VIEW_ACTION_AUDIT,
    ],
    Role.ANALYST: [
        Permission.READ_DATA,
        Permission.RUN_ANALYSIS,
        Permission.USE_AI,
        Permission.VIEW_FINANCIALS,
        Permission.EXPORT_REPORTS,
        Permission.VIEW_LINEAGE,
        Permission.VIEW_RECONCILIATION,
        Permission.VIEW_EVENTS,
        Permission.VIEW_ACTION,
        Permission.VIEW_ACTION_AUDIT,
    ],
    Role.EXECUTIVE: [
        Permission.READ_DATA,
        Permission.USE_AI,
        Permission.VIEW_FINANCIALS,
        Permission.EXPORT_REPORTS,
        Permission.VIEW_RECONCILIATION,
        Permission.VIEW_EVENTS,
        Permission.APPROVE_ACTION,
        Permission.VIEW_ACTION,
        Permission.VIEW_ACTION_AUDIT,
    ],
    Role.AI_AGENT: [
        Permission.READ_DATA,
        Permission.RUN_ANALYSIS,
        Permission.USE_AI,
        Permission.VIEW_LINEAGE,
        Permission.VIEW_EVENTS,
        Permission.VIEW_ACTION,
    ],
    Role.VIEWER: [
        Permission.READ_DATA,
        Permission.VIEW_EVENTS,
        Permission.VIEW_ACTION,
    ],
}

# Alias for Phase 10 backwards compatibility
ROLE_PERMISSIONS: Dict[Role, List[Permission]] = DEFAULT_ROLE_PERMISSIONS


class UserIdentity(BaseModel):
    """User identification model."""
    user_id: str = "default_user"
    username: Optional[str] = None
    email: Optional[str] = None
    roles: List[Role] = Field(default_factory=lambda: [Role.VIEWER])
    permissions: List[Permission] = Field(default_factory=list)
    is_active: bool = True


class TenantContext(BaseModel):
    """Cryptographically resolved multi-tenant security context."""
    tenant_id: str = Field(default="default_tenant", description="Authenticated tenant identifier")
    user_id: str = Field(default="default_user", description="Authenticated user or service account identifier")
    user: UserIdentity = Field(default_factory=lambda: UserIdentity(user_id="default_user"))
    roles: List[Role] = Field(default_factory=lambda: [Role.VIEWER])
    permissions: List[Permission] = Field(default_factory=list)
    session_id: Optional[str] = None
    is_service_account: bool = False
    created_at: Optional[Union[datetime, str]] = None

    def model_post_init(self, __context: Any) -> None:
        if self.user_id == "default_user" and self.user.user_id != "default_user":
            self.user_id = self.user.user_id
        if self.user.user_id == "default_user" and self.user_id != "default_user":
            self.user.user_id = self.user_id

    def has_permission(self, permission: Permission) -> bool:
        """Checks if context or underlying user has the given permission."""
        if permission in self.permissions:
            return True
        if self.user and permission in self.user.permissions:
            return True
        for role in self.roles:
            if permission in DEFAULT_ROLE_PERMISSIONS.get(role, []):
                return True
        if self.user:
            for role in self.user.roles:
                if permission in DEFAULT_ROLE_PERMISSIONS.get(role, []):
                    return True
        return False


class TokenPayload(BaseModel):
    """JWT Claims Payload."""
    sub: str
    tenant_id: str
    roles: List[str] = Field(default_factory=list)
    permissions: List[str] = Field(default_factory=list)
    exp: Optional[int] = None
    iat: Optional[int] = None
    iss: Optional[str] = "aurix-auth-platform"


class TokenResponse(BaseModel):
    """Authentication bearer token response envelope."""
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    tenant_id: str
    user_id: str
    roles: List[Role]
    permissions: List[Permission]


class UserProfile(BaseModel):
    """User profile metadata."""
    user_id: str
    tenant_id: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    roles: List[Role] = Field(default_factory=list)
    permissions: List[Permission] = Field(default_factory=list)
    is_active: bool = True
    created_at: Optional[datetime] = None