"""Phase 22 Enterprise Sales & Commercial Intelligence tables and RLS policies

Revision ID: 0012_phase22_commercial_intelligence
Revises: 0011_phase21_business_finance_intelligence
Create Date: 2026-08-22 03:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0012_phase22_commercial_intelligence'
down_revision = '0011_phase21_business_finance_intelligence'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Commercial Targets Table
    op.create_table(
        'commercial_targets',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('tenant_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('period_key', sa.String(length=64), nullable=False, index=True),
        sa.Column('target_revenue', sa.Float(), nullable=False),
        sa.Column('target_gross_margin_pct', sa.Float(), nullable=False, default=35.0),
        sa.Column('target_otif_pct', sa.Float(), nullable=False, default=95.0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # 2. Commercial Account Snapshots Table
    op.create_table(
        'commercial_account_snapshots',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('tenant_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('customer_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('pareto_tier', sa.String(length=16), nullable=False),
        sa.Column('health_status', sa.String(length=32), nullable=False),
        sa.Column('health_score', sa.Float(), nullable=False),
        sa.Column('period_revenue', sa.Float(), nullable=False),
        sa.Column('order_count', sa.Integer(), nullable=False),
        sa.Column('evaluated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # 3. Commercial Anomalies Table
    op.create_table(
        'commercial_anomalies',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('tenant_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('domain', sa.String(length=64), nullable=False, index=True),
        sa.Column('severity', sa.String(length=32), nullable=False, index=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('impact_amount', sa.Float(), nullable=False, default=0.0),
        sa.Column('entity_id', sa.String(length=128), nullable=False),
        sa.Column('detected_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # 4. Enable Row Level Security & Policies
    tables = ['commercial_targets', 'commercial_account_snapshots', 'commercial_anomalies']
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
    tables = ['commercial_anomalies', 'commercial_account_snapshots', 'commercial_targets']
    for table in tables:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_policy ON {table};")
        op.drop_table(table)
