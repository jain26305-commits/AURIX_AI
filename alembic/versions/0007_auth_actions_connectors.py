"""Add persistent auth, tenant, actions, and connector models with RLS.

Revision ID: 0007_auth_actions_connectors
Revises: 0006_phase16_final_hardening
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0007_auth_actions_connectors"
down_revision: Union[str, None] = "0006_phase16_final_hardening"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_RLS_TABLES = [
    "tenant_memberships",
    "user_sessions",
    "phase14_actions",
    "connectors",
]

def _json_type() -> sa.types.TypeEngine:
    return sa.JSON().with_variant(postgresql.JSONB(), "postgresql")

def upgrade() -> None:
    json_col = _json_type()

    # 1. Tenants Table
    op.create_table(
        "tenants",
        sa.Column("id", sa.String(length=64), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("plan", sa.String(length=64), nullable=False, server_default="ENTERPRISE"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="ACTIVE"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_tenants_id", "tenants", ["id"])

    # 2. Users Table
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=64), primary_key=True, nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_superuser", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_email", "users", ["email"])

    # 3. Tenant Memberships Table
    op.create_table(
        "tenant_memberships",
        sa.Column("id", sa.String(length=64), primary_key=True, nullable=False),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("role", sa.String(length=64), nullable=False, server_default="SUPPLY_CHAIN_ANALYST"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "user_id", name="uq_tenant_user_membership"),
    )
    op.create_index("ix_tenant_memberships_id", "tenant_memberships", ["id"])
    op.create_index("ix_tenant_memberships_tenant_id", "tenant_memberships", ["tenant_id"])
    op.create_index("ix_tenant_memberships_user_id", "tenant_memberships", ["user_id"])

    # 4. User Sessions Table
    op.create_table(
        "user_sessions",
        sa.Column("id", sa.String(length=64), primary_key=True, nullable=False),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("session_token", sa.String(length=512), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_user_sessions_id", "user_sessions", ["id"])
    op.create_index("ix_user_sessions_tenant_id", "user_sessions", ["tenant_id"])
    op.create_index("ix_user_sessions_user_id", "user_sessions", ["user_id"])
    op.create_index("ix_user_sessions_token", "user_sessions", ["session_token"])

    # 5. Phase 14 Actions Table
    op.create_table(
        "phase14_actions",
        sa.Column("id", sa.String(length=64), primary_key=True, nullable=False),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("domain", sa.String(length=64), nullable=False),
        sa.Column("priority", sa.String(length=32), nullable=False, server_default="NORMAL"),
        sa.Column("state", sa.String(length=32), nullable=False, server_default="AWAITING_APPROVAL"),
        sa.Column("target_entity_id", sa.String(length=64), nullable=False),
        sa.Column("target_entity_name", sa.String(length=255), nullable=False),
        sa.Column("prescriptive_payload_json", json_col, nullable=False),
        sa.Column("initiated_by", sa.String(length=128), nullable=False),
        sa.Column("assigned_approver_role", sa.String(length=64), nullable=False, server_default="SUPER_ADMIN"),
        sa.Column("preflight_cleared", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("preflight_checks_json", json_col, nullable=False),
        sa.Column("execution_token_json", json_col, nullable=True),
        sa.Column("audit_trail_json", json_col, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    for col in ["id", "tenant_id", "domain", "state", "target_entity_id"]:
        op.create_index(f"ix_phase14_actions_{col}", "phase14_actions", [col])

    # 6. Connectors Table
    op.create_table(
        "connectors",
        sa.Column("id", sa.String(length=64), primary_key=True, nullable=False),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("connector_type", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="CONNECTED"),
        sa.Column("deployment", sa.String(length=128), nullable=False),
        sa.Column("connectivity_state", sa.String(length=32), nullable=False, server_default="LIVE"),
        sa.Column("last_sync_timestamp", sa.String(length=64), nullable=False, server_default="Just now"),
        sa.Column("next_scheduled_sync", sa.String(length=64), nullable=False, server_default="in 15 minutes"),
        sa.Column("records_synced_last_24h", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_rate_percent", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("sync_frequency", sa.String(length=128), nullable=False),
        sa.Column("endpoint_masked", sa.String(length=255), nullable=False),
        sa.Column("health_note", sa.Text(), nullable=False),
        sa.Column("checkpoint", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    for col in ["id", "tenant_id", "connector_type"]:
        op.create_index(f"ix_connectors_{col}", "connectors", [col])

    # 7. Apply PostgreSQL Row-Level Security
    if op.get_bind().dialect.name == "postgresql":
        for table_name in _RLS_TABLES:
            op.execute(
                sa.text(
                    f"""
                    ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY;
                    ALTER TABLE {table_name} FORCE ROW LEVEL SECURITY;
                    DROP POLICY IF EXISTS aurix_tenant_isolation ON {table_name};
                    CREATE POLICY aurix_tenant_isolation ON {table_name}
                    USING (tenant_id = current_setting('app.tenant_id', true))
                    WITH CHECK (tenant_id = current_setting('app.tenant_id', true));
                    """
                )
            )

def downgrade() -> None:
    if op.get_bind().dialect.name == "postgresql":
        for table_name in reversed(_RLS_TABLES):
            op.execute(
                sa.text(
                    f"""
                    DROP POLICY IF EXISTS aurix_tenant_isolation ON {table_name};
                    ALTER TABLE {table_name} NO FORCE ROW LEVEL SECURITY;
                    ALTER TABLE {table_name} DISABLE ROW LEVEL SECURITY;
                    """
                )
            )

    op.drop_table("connectors")
    op.drop_table("phase14_actions")
    op.drop_table("user_sessions")
    op.drop_table("tenant_memberships")
    op.drop_table("users")
    op.drop_table("tenants")