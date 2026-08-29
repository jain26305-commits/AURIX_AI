"""Normalize Phase 21-23 tenant RLS policies.

Revision ID: 0022_phase32_phase21_23_rls_cleanup
Revises: 0021_phase32_schema_security_reconciliation
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "0022_phase32_phase21_23_rls_cleanup"
down_revision: Union[str, None] = "0021_phase32_schema_security_reconciliation"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_TABLES = [
    "commercial_account_snapshots",
    "commercial_anomalies",
    "commercial_targets",
    "financial_anomalies",
    "financial_configurations",
    "financial_snapshots",
    "machine_downtimes",
    "oee_snapshots",
    "quality_events",
    "work_centers",
]


def upgrade() -> None:
    if op.get_bind().dialect.name != "postgresql":
        return

    for table_name in _TABLES:
        op.execute(
            sa.text(
                f"""
                ALTER TABLE {table_name}
                ENABLE ROW LEVEL SECURITY;

                ALTER TABLE {table_name}
                FORCE ROW LEVEL SECURITY;

                DROP POLICY IF EXISTS tenant_isolation_policy
                ON {table_name};

                DROP POLICY IF EXISTS aurix_tenant_isolation
                ON {table_name};

                CREATE POLICY aurix_tenant_isolation
                ON {table_name}
                USING (
                    tenant_id = current_setting('app.tenant_id', true)
                )
                WITH CHECK (
                    tenant_id = current_setting('app.tenant_id', true)
                );
                """
            )
        )


def downgrade() -> None:
    if op.get_bind().dialect.name != "postgresql":
        return

    for table_name in _TABLES:
        op.execute(
            sa.text(
                f"""
                DROP POLICY IF EXISTS aurix_tenant_isolation
                ON {table_name};

                ALTER TABLE {table_name}
                NO FORCE ROW LEVEL SECURITY;
                """
            )
        )
