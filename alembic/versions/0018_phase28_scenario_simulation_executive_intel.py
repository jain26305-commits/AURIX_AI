"""Phase 28 Scenario Simulation, Executive Intelligence & Outcome Learning tables with PostgreSQL RLS

Revision ID: 0018_phase28_scenarios
Revises: 0017_phase27_decision_engine
Create Date: 2026-08-23 03:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0018_phase28_scenarios'
down_revision = '0017_phase27_decision_engine'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Scenarios Table
    op.create_table(
        'scenarios',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('tenant_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('scenario_type', sa.String(length=64), nullable=False, index=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False, default=''),
        sa.Column('baseline_reference', sa.String(length=128), nullable=False, default='CURRENT_OPERATIONAL_BASELINE'),
        sa.Column('time_horizon_days', sa.Integer(), nullable=False, default=90),
        sa.Column('status', sa.String(length=32), nullable=False, default='READY', index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # 2. Scenario Assumptions Table
    op.create_table(
        'scenario_assumptions',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('tenant_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('scenario_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('parameter_name', sa.String(length=128), nullable=False),
        sa.Column('baseline_value', sa.Float(), nullable=False),
        sa.Column('perturbed_value', sa.Float(), nullable=False),
        sa.Column('unit', sa.String(length=32), nullable=False, default='PERCENT'),
        sa.Column('justification', sa.Text(), nullable=True),
    )

    # 3. Scenario Results Table
    op.create_table(
        'scenario_results',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('tenant_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('scenario_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('simulated_revenue_usd', sa.Float(), nullable=False, default=0.0),
        sa.Column('simulated_margin_usd', sa.Float(), nullable=False, default=0.0),
        sa.Column('simulated_working_capital_usd', sa.Float(), nullable=False, default=0.0),
        sa.Column('simulated_risk_exposure_usd', sa.Float(), nullable=False, default=0.0),
        sa.Column('expected_value_usd', sa.Float(), nullable=False, default=0.0, index=True),
        sa.Column('confidence_score', sa.Float(), nullable=False, default=0.90),
        sa.Column('p50_usd', sa.Float(), nullable=False, default=0.0),
        sa.Column('p80_usd', sa.Float(), nullable=False, default=0.0),
        sa.Column('p90_usd', sa.Float(), nullable=False, default=0.0),
        sa.Column('tradeoffs_json', sa.JSON(), nullable=True),
        sa.Column('executed_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # 4. Counterfactual Records Table
    op.create_table(
        'counterfactual_records',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('tenant_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('entity_type', sa.String(length=64), nullable=False, index=True),
        sa.Column('entity_id', sa.String(length=128), nullable=False, index=True),
        sa.Column('historical_event_ref', sa.String(length=128), nullable=False, index=True),
        sa.Column('methodology', sa.String(length=128), nullable=False),
        sa.Column('observed_outcome_usd', sa.Float(), nullable=False),
        sa.Column('counterfactual_outcome_usd', sa.Float(), nullable=False),
        sa.Column('net_impact_usd', sa.Float(), nullable=False, index=True),
        sa.Column('limitations_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # 5. Outcome Tracking Table
    op.create_table(
        'outcome_tracking',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('tenant_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('decision_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('action_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('predicted_value_usd', sa.Float(), nullable=False),
        sa.Column('actual_value_usd', sa.Float(), nullable=False),
        sa.Column('prediction_error_usd', sa.Float(), nullable=False, default=0.0),
        sa.Column('value_realization_pct', sa.Float(), nullable=False, default=0.0),
        sa.Column('error_cause', sa.String(length=128), nullable=False, default='NONE'),
        sa.Column('observed_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # 6. Confidence Calibration Table
    op.create_table(
        'confidence_calibration',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('tenant_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('domain', sa.String(length=64), nullable=False, index=True),
        sa.Column('predicted_confidence_avg', sa.Float(), nullable=False),
        sa.Column('actual_accuracy_avg', sa.Float(), nullable=False),
        sa.Column('calibration_error', sa.Float(), nullable=False),
        sa.Column('calibrated_weight_factor', sa.Float(), nullable=False, default=1.0),
        sa.Column('evaluated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # Enable Row Level Security on all tenant tables
    tenant_tables = [
        'scenarios',
        'scenario_assumptions',
        'scenario_results',
        'counterfactual_records',
        'outcome_tracking',
        'confidence_calibration',
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
        'confidence_calibration',
        'outcome_tracking',
        'counterfactual_records',
        'scenario_results',
        'scenario_assumptions',
        'scenarios',
    ]
    for table in tables:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_policy ON {table};")
        op.drop_table(table)
