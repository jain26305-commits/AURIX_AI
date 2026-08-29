"""Enforce RLS on ai_usage_policies and ensure strict tenant isolation policies.

Revision ID: 0008_enforce_rls_policies
Revises: 0007_auth_actions_connectors
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0008_enforce_rls_policies"
down_revision: Union[str, None] = "0007_auth_actions_connectors"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLES = [
    "ai_usage_policies",
    "ai_audit_logs",
    "ai_usage_ledgers",
    "phase14_actions",
    "connectors",
    "phase16_cases",
]

def upgrade() -> None:
    if op.get_bind().dialect.name == "postgresql":
        for table_name in _TABLES:
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
        for table_name in reversed(_TABLES):
            op.execute(
                sa.text(
                    f"""
                    DROP POLICY IF EXISTS aurix_tenant_isolation ON {table_name};
                    ALTER TABLE {table_name} NO FORCE ROW LEVEL SECURITY;
                    ALTER TABLE {table_name} DISABLE ROW LEVEL SECURITY;
                    """
                )
            )