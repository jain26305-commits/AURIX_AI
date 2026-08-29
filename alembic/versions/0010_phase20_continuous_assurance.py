"""Phase 20 Continuous Assurance Engine tables and RLS policies

Revision ID: 0010_phase20_continuous_assurance
Revises: 0009_phase19_enterprise_data_fabric
Create Date: 2026-08-22 01:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0010_phase20_continuous_assurance'
down_revision = '0009_phase19_enterprise_data_fabric'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Assurance Findings Table
    op.create_table(
        'assurance_findings',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('tenant_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('domain', sa.String(length=64), nullable=False, index=True),
        sa.Column('severity', sa.String(length=32), nullable=False, index=True),
        sa.Column('status', sa.String(length=32), nullable=False, default='OPEN'),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('financial_exposure', sa.Float(), nullable=False, default=0.0),
        sa.Column('currency', sa.String(length=16), nullable=False, default='USD'),
        sa.Column('entity_type', sa.String(length=64), nullable=False),
        sa.Column('entity_id', sa.String(length=128), nullable=False),
        sa.Column('evidence_data', sa.JSON(), nullable=True),
        sa.Column('recommended_action', sa.Text(), nullable=True),
        sa.Column('detected_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # 2. Assurance Runs Table
    op.create_table(
        'assurance_runs',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('tenant_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('total_findings', sa.Integer(), nullable=False, default=0),
        sa.Column('total_financial_leakage', sa.Float(), nullable=False, default=0.0),
        sa.Column('critical_findings_count', sa.Integer(), nullable=False, default=0),
        sa.Column('high_findings_count', sa.Integer(), nullable=False, default=0),
        sa.Column('domain_breakdown', sa.JSON(), nullable=True),
        sa.Column('executed_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # 3. Assurance Rules Table
    op.create_table(
        'assurance_rules',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('tenant_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('rule_code', sa.String(64), nullable=False, index=True),
        sa.Column('domain', sa.String(length=64), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('parameters', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # 4. Enable Row Level Security & Attach Policies
    tables = ['assurance_findings', 'assurance_runs', 'assurance_rules']
    for table in tables:
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
    tables = ['assurance_rules', 'assurance_runs', 'assurance_findings']
    for table in tables:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_policy ON {table};")
        op.drop_table(table)
