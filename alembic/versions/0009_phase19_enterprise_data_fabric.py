"""Phase 19 Enterprise Data Fabric tables and RLS policies

Revision ID: 0009_phase19_enterprise_data_fabric
Revises: 0008_enforce_rls_policies
Create Date: 2026-08-22 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0009_phase19_enterprise_data_fabric'
down_revision = '0008_enforce_rls_policies'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Sync Checkpoints Table
    op.create_table(
        'data_fabric_checkpoints',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('tenant_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('connector_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('stream_name', sa.String(length=128), nullable=False),
        sa.Column('cursor_field', sa.String(length=128), nullable=True),
        sa.Column('cursor_value', sa.String(length=256), nullable=True),
        sa.Column('high_watermark', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rows_synced_total', sa.BigInteger(), default=0),
        sa.Column('last_successful_sync_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_attempted_sync_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('state_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # 2. Entity Aliases Table
    op.create_table(
        'entity_aliases',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('tenant_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('canonical_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('canonical_entity_type', sa.String(length=64), nullable=False),
        sa.Column('source_system', sa.String(length=64), nullable=False),
        sa.Column('source_record_id', sa.String(length=256), nullable=False),
        sa.Column('confidence_score', sa.Float(), default=1.0),
        sa.Column('resolution_rule', sa.String(length=128), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # 3. Schema Drift Logs Table
    op.create_table(
        'schema_drift_logs',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('tenant_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('connector_id', sa.String(length=64), nullable=False),
        sa.Column('stream_name', sa.String(length=128), nullable=False),
        sa.Column('drift_type', sa.String(length=64), nullable=False),
        sa.Column('field_name', sa.String(length=128), nullable=False),
        sa.Column('expected_type', sa.String(length=64), nullable=True),
        sa.Column('detected_type', sa.String(length=64), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('acknowledged', sa.Boolean(), default=False),
        sa.Column('detected_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # 4. Source Authority Rules Table
    op.create_table(
        'source_authority_rules',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('tenant_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('canonical_entity_type', sa.String(length=64), nullable=False),
        sa.Column('attribute_name', sa.String(length=128), nullable=True),
        sa.Column('precedence_order', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # 5. Enable Row Level Security & Isolation Policies
    tables = [
        'data_fabric_checkpoints',
        'entity_aliases',
        'schema_drift_logs',
        'source_authority_rules',
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
        'source_authority_rules',
        'schema_drift_logs',
        'entity_aliases',
        'data_fabric_checkpoints',
    ]
    for table in tables:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_policy ON {table};")
        op.drop_table(table)
