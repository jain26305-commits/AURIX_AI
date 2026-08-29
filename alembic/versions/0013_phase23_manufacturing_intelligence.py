"""Phase 23 Manufacturing & Production Intelligence tables and RLS policies

Revision ID: 0013_phase23_manufacturing_intelligence
Revises: 0012_phase22_commercial_intelligence
Create Date: 2026-08-22 04:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0013_phase23_manufacturing_intelligence'
down_revision = '0012_phase22_commercial_intelligence'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Work Centers Table
    op.create_table(
        'work_centers',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('tenant_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('plant_location_id', sa.String(length=64), nullable=False),
        sa.Column('capacity_hours_per_day', sa.Float(), nullable=False, default=16.0),
        sa.Column('is_bottleneck', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # 2. Machine Downtimes Table
    op.create_table(
        'machine_downtimes',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('tenant_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('work_center_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('machine_id', sa.String(length=64), nullable=True),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_minutes', sa.Float(), nullable=False, default=0.0),
        sa.Column('reason_code', sa.String(length=64), nullable=False),
        sa.Column('is_planned', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # 3. Quality Events Table
    op.create_table(
        'quality_events',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('tenant_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('work_order_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('sku_id', sa.String(length=64), nullable=False),
        sa.Column('scrap_quantity', sa.Float(), nullable=False, default=0.0),
        sa.Column('defect_reason', sa.String(length=128), nullable=True),
        sa.Column('rework_hours', sa.Float(), nullable=False, default=0.0),
        sa.Column('recorded_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # 4. OEE Snapshots Table
    op.create_table(
        'oee_snapshots',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('tenant_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('work_center_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('period_key', sa.String(length=64), nullable=False),
        sa.Column('availability_pct', sa.Float(), nullable=True),
        sa.Column('performance_pct', sa.Float(), nullable=True),
        sa.Column('quality_pct', sa.Float(), nullable=True),
        sa.Column('oee_pct', sa.Float(), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False, default='AVAILABLE'),
        sa.Column('evaluated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # 5. Enable Row Level Security & Policies
    tables = ['work_centers', 'machine_downtimes', 'quality_events', 'oee_snapshots']
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
    tables = ['oee_snapshots', 'quality_events', 'machine_downtimes', 'work_centers']
    for table in tables:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_policy ON {table};")
        op.drop_table(table)
