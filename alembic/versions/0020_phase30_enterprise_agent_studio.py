"""Phase 30 Enterprise Agent Studio & Workflow Orchestration tables with PostgreSQL RLS

Revision ID: 0020_phase30_agent_studio
Revises: 0019_phase29_governed_agents
Create Date: 2026-08-23 05:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = '0020_phase30_agent_studio'
down_revision = '0019_phase29_governed_agents'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Studio Agents Table
    op.create_table(
        'studio_agents',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('tenant_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('business_purpose', sa.Text(), nullable=False, default=''),
        sa.Column('domain', sa.String(length=64), nullable=False, default='SUPPLY_CHAIN'),
        sa.Column('owner', sa.String(length=128), nullable=False, default='ADMIN'),
        sa.Column('agent_type', sa.String(length=64), nullable=False, default='PROCUREMENT_AGENT'),
        sa.Column('version', sa.String(length=32), nullable=False, default='1.0.0'),
        sa.Column('status', sa.String(length=32), nullable=False, default='DRAFT', index=True),
        sa.Column('allowed_skills_json', sa.JSON(), nullable=True),
        sa.Column('allowed_tools_json', sa.JSON(), nullable=True),
        sa.Column('context_domains_json', sa.JSON(), nullable=True),
        sa.Column('risk_classification', sa.String(length=32), nullable=False, default='MEDIUM'),
        sa.Column('max_steps', sa.Integer(), nullable=False, default=10),
        sa.Column('budget_limit_usd', sa.Float(), nullable=False, default=1000.0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # 2. Studio Agent Versions Table
    op.create_table(
        'studio_agent_versions',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('tenant_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('agent_id', sa.String(length=64), sa.ForeignKey('studio_agents.id'), nullable=False, index=True),
        sa.Column('version_number', sa.String(length=32), nullable=False, index=True),
        sa.Column('status', sa.String(length=32), nullable=False, default='PUBLISHED'),
        sa.Column('config_snapshot_json', sa.JSON(), nullable=False),
        sa.Column('published_by', sa.String(length=128), nullable=False),
        sa.Column('change_summary', sa.Text(), nullable=True),
        sa.Column('published_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # 3. Studio Workflows Table
    op.create_table(
        'studio_workflows',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('tenant_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False, default=''),
        sa.Column('version', sa.String(length=32), nullable=False, default='1.0.0'),
        sa.Column('status', sa.String(length=32), nullable=False, default='DRAFT'),
        sa.Column('triggers_json', sa.JSON(), nullable=True),
        sa.Column('nodes_json', sa.JSON(), nullable=True),
        sa.Column('edges_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # 4. Studio Workflow Versions Table
    op.create_table(
        'studio_workflow_versions',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('tenant_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('workflow_id', sa.String(length=64), sa.ForeignKey('studio_workflows.id'), nullable=False, index=True),
        sa.Column('version_number', sa.String(length=32), nullable=False),
        sa.Column('nodes_json', sa.JSON(), nullable=False),
        sa.Column('edges_json', sa.JSON(), nullable=False),
        sa.Column('published_by', sa.String(length=128), nullable=False),
        sa.Column('published_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # 5. Studio Deployments Table
    op.create_table(
        'studio_deployments',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('tenant_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('agent_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('version_id', sa.String(length=64), nullable=False),
        sa.Column('environment', sa.String(length=32), nullable=False, default='PRODUCTION', index=True),
        sa.Column('deployed_by', sa.String(length=128), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, default='ACTIVE'),
        sa.Column('deployed_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # 6. Studio Templates Table (Global)
    op.create_table(
        'studio_templates',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('template_type', sa.String(length=32), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('category', sa.String(length=64), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('definition_json', sa.JSON(), nullable=False),
    )

    # 7. Studio Audit Logs Table
    op.create_table(
        'studio_audit_logs',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('tenant_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('action_type', sa.String(length=64), nullable=False),
        sa.Column('entity_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('performed_by', sa.String(length=128), nullable=False),
        sa.Column('details_json', sa.JSON(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # Enable Row Level Security on tenant tables
    tenant_tables = [
        'studio_agents',
        'studio_agent_versions',
        'studio_workflows',
        'studio_workflow_versions',
        'studio_deployments',
        'studio_audit_logs',
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
        'studio_audit_logs',
        'studio_templates',
        'studio_deployments',
        'studio_workflow_versions',
        'studio_workflows',
        'studio_agent_versions',
        'studio_agents',
    ]
    for table in tables:
        if table != 'studio_templates':
            op.execute(f"DROP POLICY IF EXISTS tenant_isolation_policy ON {table};")
        op.drop_table(table)
