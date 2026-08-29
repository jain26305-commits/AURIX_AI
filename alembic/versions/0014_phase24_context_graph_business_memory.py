"""Phase 24 Context Graph, Business Memory & Data Contracts tables with PostgreSQL RLS

Revision ID: 0014_phase24_context_graph
Revises: 0013_phase23_manufacturing_intelligence
Create Date: 2026-08-22 05:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0014_phase24_context_graph'
down_revision = '0013_phase23_manufacturing_intelligence'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Context Nodes Table
    op.create_table(
        'context_nodes',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('tenant_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('entity_type', sa.String(length=64), nullable=False, index=True),
        sa.Column('canonical_id', sa.String(length=128), nullable=False, index=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('attributes_json', sa.JSON(), nullable=True),
        sa.Column('source_system', sa.String(length=64), nullable=False, default='AURIX_FABRIC'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # 2. Context Edges Table
    op.create_table(
        'context_edges',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('tenant_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('source_node_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('target_node_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('relationship_type', sa.String(length=64), nullable=False, index=True),
        sa.Column('confidence_level', sa.String(length=32), nullable=False, default='OBSERVED'),
        sa.Column('relationship_status', sa.String(length=32), nullable=False, default='ACTIVE'),
        sa.Column('weight', sa.Float(), nullable=False, default=1.0),
        sa.Column('evidence_json', sa.JSON(), nullable=True),
        sa.Column('effective_from', sa.DateTime(timezone=True), nullable=True),
        sa.Column('effective_to', sa.DateTime(timezone=True), nullable=True),
    )

    # 3. Business Memories Table
    op.create_table(
        'business_memories',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('tenant_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('category', sa.String(length=64), nullable=False, index=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('context_entity_id', sa.String(length=128), nullable=True, index=True),
        sa.Column('decision_action_id', sa.String(length=128), nullable=True, index=True),
        sa.Column('outcome_status', sa.String(length=64), nullable=False, default='PENDING_EVALUATION'),
        sa.Column('lessons_learned', sa.Text(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=False, default=1.0),
        sa.Column('recorded_by', sa.String(length=64), nullable=False, default='SYSTEM_GOVERNANCE'),
        sa.Column('recorded_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # 4. Data Contracts Table
    op.create_table(
        'data_contracts',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('tenant_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('dataset_name', sa.String(length=128), nullable=False, index=True),
        sa.Column('schema_version', sa.String(length=32), nullable=False, default='v1.0'),
        sa.Column('owner_domain', sa.String(length=64), nullable=False),
        sa.Column('freshness_slo_seconds', sa.Integer(), nullable=False, default=3600),
        sa.Column('quality_slo_pct', sa.Float(), nullable=False, default=98.0),
        sa.Column('consumers_json', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False, default='ACTIVE'),
    )

    # 5. Business DNA Snapshots Table
    op.create_table(
        'business_dna_snapshots',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('tenant_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('period_key', sa.String(length=64), nullable=False, index=True),
        sa.Column('operating_model', sa.String(length=128), nullable=False),
        sa.Column('customer_concentration_hhi', sa.Float(), nullable=False),
        sa.Column('supplier_concentration_hhi', sa.Float(), nullable=False),
        sa.Column('inventory_intensity_pct', sa.Float(), nullable=False),
        sa.Column('working_capital_intensity_pct', sa.Float(), nullable=False),
        sa.Column('manufacturing_complexity_tier', sa.String(length=32), nullable=False),
        sa.Column('evaluated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # 6. Enable Row Level Security & Isolation Policies
    tables = ['context_nodes', 'context_edges', 'business_memories', 'data_contracts', 'business_dna_snapshots']
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
    tables = ['business_dna_snapshots', 'data_contracts', 'business_memories', 'context_edges', 'context_nodes']
    for table in tables:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_policy ON {table};")
        op.drop_table(table)
