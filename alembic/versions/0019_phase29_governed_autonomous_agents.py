"""Phase 29 Governed Autonomous Agents tables with PostgreSQL RLS

Revision ID: 0019_phase29_governed_agents
Revises: 0018_phase28_scenarios
Create Date: 2026-08-23 04:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0019_phase29_governed_agents'
down_revision = '0018_phase28_scenarios'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Skill Registry Table (Global)
    op.create_table(
        'skill_registries',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('name', sa.String(length=128), nullable=False, index=True),
        sa.Column('version', sa.String(length=32), nullable=False, default='v1.0'),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('risk_level', sa.String(length=32), nullable=False, default='MEDIUM'),
        sa.Column('requires_approval', sa.Boolean(), nullable=False, default=False),
        sa.Column('side_effect', sa.String(length=32), nullable=False, default='REVERSIBLE'),
    )

    # 2. Tool Registry Table (Global)
    op.create_table(
        'tool_registries',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('name', sa.String(length=128), nullable=False, index=True),
        sa.Column('version', sa.String(length=32), nullable=False, default='v1.0'),
        sa.Column('endpoint_ref', sa.String(length=255), nullable=False),
        sa.Column('risk_level', sa.String(length=32), nullable=False, default='MEDIUM'),
        sa.Column('rate_limit_per_min', sa.Integer(), nullable=False, default=60),
    )

    # 3. Agent Runtimes Table (Tenant-scoped)
    op.create_table(
        'agent_runtimes',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('tenant_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('agent_type', sa.String(length=64), nullable=False, index=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('version', sa.String(length=32), nullable=False, default='v1.0'),
        sa.Column('status', sa.String(length=32), nullable=False, default='ACTIVE', index=True),
        sa.Column('owner', sa.String(length=128), nullable=False),
        sa.Column('capabilities_json', sa.JSON(), nullable=True),
        sa.Column('risk_classification', sa.String(length=32), nullable=False, default='MEDIUM'),
        sa.Column('max_steps', sa.Integer(), nullable=False, default=10),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # 4. Agent Execution Journals Table (Tenant-scoped)
    op.create_table(
        'agent_execution_journals',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('tenant_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('agent_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('plan_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('idempotency_key', sa.String(length=128), nullable=False, unique=True, index=True),
        sa.Column('state', sa.String(length=32), nullable=False, default='PLANNED', index=True),
        sa.Column('risk_level', sa.String(length=32), nullable=False, default='MEDIUM'),
        sa.Column('inputs_json', sa.JSON(), nullable=True),
        sa.Column('outputs_json', sa.JSON(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    )

    # 5. Value Network Records Table (Tenant-scoped)
    op.create_table(
        'value_network_records',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('tenant_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('execution_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('decision_ref', sa.String(length=64), nullable=True, index=True),
        sa.Column('value_attribution_type', sa.String(length=64), nullable=False, index=True),
        sa.Column('realized_value_usd', sa.Float(), nullable=False, default=0.0, index=True),
        sa.Column('verified', sa.Boolean(), nullable=False, default=True),
        sa.Column('recorded_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # Enable Row Level Security on tenant tables
    tenant_tables = [
        'agent_runtimes',
        'agent_execution_journals',
        'value_network_records',
    ]
    for table in tenant_tables:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
        op.execute(
            f"""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_policies WHERE tablename = '{table}' AND policyname = 'tenant_isolation_policy'
                ) THEN
                    CREATE POLICY tenant_isolation_policy ON {table}
                        AS RESTRICTIVE
                        USING (tenant_id = current_setting('app.current_tenant_id', true));
                END IF;
            END
            $$;
            """
        )


def downgrade() -> None:
    tables = [
        'value_network_records',
        'agent_execution_journals',
        'agent_runtimes',
        'tool_registries',
        'skill_registries',
    ]
    for table in tables:
        if table not in ('tool_registries', 'skill_registries'):
            op.execute(f"DROP POLICY IF EXISTS tenant_isolation_policy ON {table};")
        op.drop_table(table)
