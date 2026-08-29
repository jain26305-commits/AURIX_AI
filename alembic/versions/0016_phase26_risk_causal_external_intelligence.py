"""Phase 26 Risk, Causal & External Intelligence tables with PostgreSQL RLS

Revision ID: 0016_phase26_risk_intelligence
Revises: 0015_phase25_process_intelligence_ocpm
Create Date: 2026-08-23 01:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0016_phase26_risk_intelligence'
down_revision = '0015_phase25_process_intelligence_ocpm'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. External Signals Table (Global reference feed)
    op.create_table(
        'external_signals',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('source_name', sa.String(length=128), nullable=False, index=True),
        sa.Column('source_record_id', sa.String(length=128), nullable=False, index=True),
        sa.Column('signal_type', sa.String(length=64), nullable=False, index=True),
        sa.Column('geography', sa.String(length=64), nullable=False, index=True),
        sa.Column('severity', sa.String(length=32), nullable=False, default='MEDIUM'),
        sa.Column('confidence', sa.Float(), nullable=False, default=0.95),
        sa.Column('metric_value', sa.Float(), nullable=False, default=0.0),
        sa.Column('metric_unit', sa.String(length=32), nullable=False, default='INDEX'),
        sa.Column('currency', sa.String(length=16), nullable=False, default='USD'),
        sa.Column('observed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), index=True),
        sa.Column('valid_from', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('valid_to', sa.DateTime(timezone=True), nullable=True),
        sa.Column('raw_payload_json', sa.JSON(), nullable=True),
    )

    # 2. Risk Findings Table (Tenant-scoped)
    op.create_table(
        'risk_findings',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('tenant_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('risk_domain', sa.String(length=64), nullable=False, index=True),
        sa.Column('entity_type', sa.String(length=64), nullable=False, index=True),
        sa.Column('entity_id', sa.String(length=128), nullable=False, index=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('probability', sa.Float(), nullable=False, default=0.5),
        sa.Column('impact_amount', sa.Float(), nullable=False, default=0.0),
        sa.Column('exposure_amount', sa.Float(), nullable=False, default=0.0),
        sa.Column('priority_score', sa.Float(), nullable=False, default=0.0, index=True),
        sa.Column('urgency_hours', sa.Float(), nullable=False, default=24.0),
        sa.Column('confidence_level', sa.Float(), nullable=False, default=0.9),
        sa.Column('status', sa.String(length=32), nullable=False, default='ACTIVE', index=True),
        sa.Column('evidence_json', sa.JSON(), nullable=True),
        sa.Column('first_detected', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('last_updated', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('valid_to', sa.DateTime(timezone=True), nullable=True),
    )

    # 3. External Signal Mappings Table
    op.create_table(
        'external_signal_mappings',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('tenant_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('signal_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('entity_type', sa.String(length=64), nullable=False, index=True),
        sa.Column('entity_id', sa.String(length=128), nullable=False, index=True),
        sa.Column('mapping_rule', sa.String(length=128), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False, default=0.9),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # 4. Opportunity Findings Table
    op.create_table(
        'opportunity_findings',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('tenant_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('opportunity_type', sa.String(length=64), nullable=False, index=True),
        sa.Column('entity_type', sa.String(length=64), nullable=False, index=True),
        sa.Column('entity_id', sa.String(length=128), nullable=False, index=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('potential_value_usd', sa.Float(), nullable=False, default=0.0, index=True),
        sa.Column('probability', sa.Float(), nullable=False, default=0.85),
        sa.Column('confidence', sa.Float(), nullable=False, default=0.9),
        sa.Column('priority_rank', sa.Integer(), nullable=False, default=1),
        sa.Column('evidence_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # 5. Causal Evidence Records Table
    op.create_table(
        'causal_evidence_records',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('tenant_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('cause_entity_id', sa.String(length=128), nullable=False, index=True),
        sa.Column('effect_entity_id', sa.String(length=128), nullable=False, index=True),
        sa.Column('relationship_classification', sa.String(length=64), nullable=False, index=True),
        sa.Column('methodology', sa.String(length=128), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=False, default=0.95),
        sa.Column('confounders_json', sa.JSON(), nullable=True),
        sa.Column('evidence_json', sa.JSON(), nullable=True),
        sa.Column('evaluated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # Enable Row Level Security on tenant tables
    tenant_tables = [
        'risk_findings',
        'external_signal_mappings',
        'opportunity_findings',
        'causal_evidence_records',
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
        'causal_evidence_records',
        'opportunity_findings',
        'external_signal_mappings',
        'risk_findings',
        'external_signals',
    ]
    for table in tables:
        if table != 'external_signals':
            op.execute(f"DROP POLICY IF EXISTS tenant_isolation_policy ON {table};")
        op.drop_table(table)
