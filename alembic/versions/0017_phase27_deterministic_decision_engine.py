"""Phase 27 Deterministic Decision Engine 2.0 tables with PostgreSQL RLS

Revision ID: 0017_phase27_decision_engine
Revises: 0016_phase26_risk_intelligence
Create Date: 2026-08-23 02:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0017_phase27_decision_engine'
down_revision = '0016_phase26_risk_intelligence'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Model Registry Table (Global)
    op.create_table(
        'model_registry',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('model_name', sa.String(length=128), nullable=False, index=True),
        sa.Column('version', sa.String(length=32), nullable=False, index=True),
        sa.Column('model_type', sa.String(length=64), nullable=False, index=True),
        sa.Column('metrics_json', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False, default='PRODUCTION'),
        sa.Column('is_champion', sa.Boolean(), nullable=False, default=True),
        sa.Column('training_dataset_ref', sa.String(length=128), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('promoted_at', sa.DateTime(timezone=True), nullable=True),
    )

    # 2. Decisions Table (Tenant-scoped)
    op.create_table(
        'decisions',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('tenant_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('decision_domain', sa.String(length=64), nullable=False, index=True),
        sa.Column('decision_type', sa.String(length=64), nullable=False, index=True),
        sa.Column('entity_type', sa.String(length=64), nullable=False, index=True),
        sa.Column('entity_id', sa.String(length=128), nullable=False, index=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('recommended_action', sa.String(length=255), nullable=False),
        sa.Column('expected_value_usd', sa.Float(), nullable=False, default=0.0),
        sa.Column('downside_risk_usd', sa.Float(), nullable=False, default=0.0),
        sa.Column('confidence_score', sa.Float(), nullable=False, default=0.9),
        sa.Column('model_id', sa.String(length=64), nullable=False, default='AURIX_DETERMINISTIC_SOLVER'),
        sa.Column('model_version', sa.String(length=32), nullable=False, default='v2.0'),
        sa.Column('status', sa.String(length=32), nullable=False, default='PROPOSED', index=True),
        sa.Column('approval_status', sa.String(length=32), nullable=False, default='PENDING', index=True),
        sa.Column('evidence_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('valid_to', sa.DateTime(timezone=True), nullable=True),
    )

    # 3. Decision Candidates Table
    op.create_table(
        'decision_candidates',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('tenant_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('decision_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('action_code', sa.String(length=64), nullable=False),
        sa.Column('action_name', sa.String(length=255), nullable=False),
        sa.Column('expected_value_usd', sa.Float(), nullable=False, default=0.0),
        sa.Column('cost_usd', sa.Float(), nullable=False, default=0.0),
        sa.Column('risk_penalty_usd', sa.Float(), nullable=False, default=0.0),
        sa.Column('utility_score', sa.Float(), nullable=False, default=0.0, index=True),
        sa.Column('is_recommended', sa.Boolean(), nullable=False, default=False),
        sa.Column('constraints_satisfied_json', sa.JSON(), nullable=True),
    )

    # 4. Decision Policies Table
    op.create_table(
        'decision_policies',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('tenant_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('policy_name', sa.String(length=128), nullable=False, index=True),
        sa.Column('decision_domain', sa.String(length=64), nullable=False, index=True),
        sa.Column('conditions_json', sa.JSON(), nullable=True),
        sa.Column('required_approver_role', sa.String(length=64), nullable=False, default='OPERATIONS_MANAGER'),
        sa.Column('auto_executable', sa.Boolean(), nullable=False, default=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # 5. Shadow Evaluations Table
    op.create_table(
        'shadow_evaluations',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('tenant_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('decision_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('champion_model_id', sa.String(length=64), nullable=False),
        sa.Column('challenger_model_id', sa.String(length=64), nullable=False),
        sa.Column('champion_output_json', sa.JSON(), nullable=True),
        sa.Column('challenger_output_json', sa.JSON(), nullable=True),
        sa.Column('variance_score', sa.Float(), nullable=False, default=0.0),
        sa.Column('evaluated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # 6. Decision Overrides Table
    op.create_table(
        'decision_overrides',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('tenant_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('decision_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('user_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('user_role', sa.String(length=64), nullable=False),
        sa.Column('action_taken', sa.String(length=64), nullable=False),
        sa.Column('override_reason', sa.Text(), nullable=False),
        sa.Column('modified_action_json', sa.JSON(), nullable=True),
        sa.Column('recorded_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # 7. Optimization Runs Table
    op.create_table(
        'optimization_runs',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('tenant_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('solver_name', sa.String(length=128), nullable=False, index=True),
        sa.Column('objective_type', sa.String(length=64), nullable=False),
        sa.Column('objective_value', sa.Float(), nullable=False, default=0.0),
        sa.Column('variables_count', sa.Integer(), nullable=False, default=0),
        sa.Column('constraints_count', sa.Integer(), nullable=False, default=0),
        sa.Column('runtime_ms', sa.Float(), nullable=False, default=0.0),
        sa.Column('status', sa.String(length=32), nullable=False, default='OPTIMAL'),
        sa.Column('result_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # Enable Row Level Security on tenant tables
    tenant_tables = [
        'decisions',
        'decision_candidates',
        'decision_policies',
        'shadow_evaluations',
        'decision_overrides',
        'optimization_runs',
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
        'optimization_runs',
        'decision_overrides',
        'shadow_evaluations',
        'decision_policies',
        'decision_candidates',
        'decisions',
        'model_registry',
    ]
    for table in tables:
        if table != 'model_registry':
            op.execute(f"DROP POLICY IF EXISTS tenant_isolation_policy ON {table};")
        op.drop_table(table)
