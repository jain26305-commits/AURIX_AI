"""Phase 21 Business Finance Intelligence tables and RLS policies

Revision ID: 0011_phase21_business_finance_intelligence
Revises: 0010_phase20_continuous_assurance
Create Date: 2026-08-22 02:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0011_phase21_business_finance_intelligence'
down_revision = '0010_phase20_continuous_assurance'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Financial Configurations Table
    op.create_table(
        'financial_configurations',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('tenant_id', sa.String(length=64), nullable=False, unique=True, index=True),
        sa.Column('fiscal_year_start_month', sa.Integer(), nullable=False, default=1),
        sa.Column('base_currency', sa.String(length=16), nullable=False, default='USD'),
        sa.Column('reporting_currency', sa.String(length=16), nullable=False, default='USD'),
        sa.Column('annual_holding_cost_rate', sa.Float(), nullable=False, default=0.22),
        sa.Column('aging_brackets', sa.JSON(), nullable=True),
        sa.Column('materiality_threshold_pct', sa.Float(), nullable=False, default=2.0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # 2. Financial Anomalies Table
    op.create_table(
        'financial_anomalies',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('tenant_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('domain', sa.String(length=64), nullable=False, index=True),
        sa.Column('severity', sa.String(length=32), nullable=False, index=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('detected_metric_value', sa.Float(), nullable=False),
        sa.Column('baseline_expected_value', sa.Float(), nullable=False),
        sa.Column('deviation_pct', sa.Float(), nullable=False),
        sa.Column('entity_id', sa.String(length=128), nullable=False),
        sa.Column('detected_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # 3. Financial Snapshots Table
    op.create_table(
        'financial_snapshots',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('tenant_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('period_key', sa.String(length=64), nullable=False, index=True),
        sa.Column('gross_revenue', sa.Float(), nullable=False),
        sa.Column('net_revenue', sa.Float(), nullable=False),
        sa.Column('cogs', sa.Float(), nullable=False),
        sa.Column('gross_profit', sa.Float(), nullable=False),
        sa.Column('gross_margin_pct', sa.Float(), nullable=False),
        sa.Column('operating_working_capital', sa.Float(), nullable=False),
        sa.Column('cash_conversion_cycle_days', sa.Float(), nullable=False),
        sa.Column('dso_days', sa.Float(), nullable=False),
        sa.Column('dpo_days', sa.Float(), nullable=False),
        sa.Column('dio_days', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # 4. Enable Row Level Security & Policies
    tables = ['financial_configurations', 'financial_anomalies', 'financial_snapshots']
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
    tables = ['financial_snapshots', 'financial_anomalies', 'financial_configurations']
    for table in tables:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_policy ON {table};")
        op.drop_table(table)
