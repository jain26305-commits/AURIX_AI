"""Phase 25 Process Intelligence & Object-Centric Process Mining tables with PostgreSQL RLS

Revision ID: 0015_phase25_process_intelligence_ocpm
Revises: 0014_phase24_context_graph
Create Date: 2026-08-23 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0015_phase25_process_intelligence_ocpm'
down_revision = '0014_phase24_context_graph'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Process Definitions Table
    op.create_table(
        'process_definitions',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('tenant_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('process_type', sa.String(length=64), nullable=False, index=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('expected_steps_json', sa.JSON(), nullable=False),
        sa.Column('sla_target_hours', sa.Float(), nullable=False, default=72.0),
        sa.Column('version', sa.String(length=32), nullable=False, default='v1.0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # 2. Process Events Table
    op.create_table(
        'process_events',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('tenant_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('process_type', sa.String(length=64), nullable=False, index=True),
        sa.Column('event_type', sa.String(length=64), nullable=False, index=True),
        sa.Column('source_system', sa.String(length=64), nullable=False, default='AURIX_FABRIC'),
        sa.Column('source_record_id', sa.String(length=128), nullable=False, index=True),
        sa.Column('actor', sa.String(length=128), nullable=True),
        sa.Column('location_id', sa.String(length=64), nullable=True),
        sa.Column('event_timestamp', sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column('attributes_json', sa.JSON(), nullable=True),
    )

    # 3. Process Object Links Table
    op.create_table(
        'process_object_links',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('tenant_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('event_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('object_type', sa.String(length=64), nullable=False, index=True),
        sa.Column('object_id', sa.String(length=128), nullable=False, index=True),
    )

    # 4. Process Variants Table
    op.create_table(
        'process_variants',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('tenant_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('process_type', sa.String(length=64), nullable=False, index=True),
        sa.Column('variant_hash', sa.String(length=64), nullable=False, index=True),
        sa.Column('step_sequence_json', sa.JSON(), nullable=False),
        sa.Column('case_count', sa.Integer(), nullable=False, default=1),
        sa.Column('average_duration_hours', sa.Float(), nullable=False, default=0.0),
        sa.Column('is_standard', sa.Boolean(), nullable=False, default=False),
    )

    # 5. Process Conformance Results Table
    op.create_table(
        'process_conformance_results',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('tenant_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('process_type', sa.String(length=64), nullable=False, index=True),
        sa.Column('case_id', sa.String(length=128), nullable=False, index=True),
        sa.Column('conformance_status', sa.String(length=64), nullable=False, index=True),
        sa.Column('deviations_json', sa.JSON(), nullable=False),
        sa.Column('evaluated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # 6. Process SLA Rules Table
    op.create_table(
        'process_sla_rules',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('tenant_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('process_type', sa.String(length=64), nullable=False, index=True),
        sa.Column('start_event_type', sa.String(length=64), nullable=False),
        sa.Column('end_event_type', sa.String(length=64), nullable=False),
        sa.Column('max_duration_hours', sa.Float(), nullable=False),
        sa.Column('severity', sa.String(length=32), nullable=False, default='HIGH'),
    )

    # 7. Process Metric Snapshots Table
    op.create_table(
        'process_metric_snapshots',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('tenant_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('period_key', sa.String(length=64), nullable=False, index=True),
        sa.Column('process_type', sa.String(length=64), nullable=False, index=True),
        sa.Column('median_cycle_time_hours', sa.Float(), nullable=False),
        sa.Column('waiting_time_pct', sa.Float(), nullable=False),
        sa.Column('rework_rate_pct', sa.Float(), nullable=False),
        sa.Column('evaluated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # Enable Row Level Security
    tables = [
        'process_definitions',
        'process_events',
        'process_object_links',
        'process_variants',
        'process_conformance_results',
        'process_sla_rules',
        'process_metric_snapshots',
    ]
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
    tables = [
        'process_metric_snapshots',
        'process_sla_rules',
        'process_conformance_results',
        'process_variants',
        'process_object_links',
        'process_events',
        'process_definitions',
    ]
    for table in tables:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_policy ON {table};")
        op.drop_table(table)
