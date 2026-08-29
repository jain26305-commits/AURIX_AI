"""Phase 32 schema and tenant-security reconciliation.

Reconciles the physically deployed PostgreSQL schema with the current
SQLAlchemy models without replaying already-existing 0014-0020 tables.

Revision ID: 0021_phase32_schema_security_reconciliation
Revises: 0020_phase30_agent_studio
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "0021_phase32_schema_security_reconciliation"
down_revision: Union[str, None] = "0020_phase30_agent_studio"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Tables that are tenant-scoped application data and should use the
# canonical AURIX transaction tenant context.
_TENANT_RLS_TABLES = [
    "advance_shipment_notice_lines",
    "advance_shipment_notices",
    "agent_execution_journals",
    "agent_runtimes",
    "ai_audit_logs",
    "ai_quota_reservations",
    "ai_usage_ledgers",
    "ai_usage_policies",
    "bom_headers",
    "bom_lines",
    "boms",
    "business_dna_snapshots",
    "business_memories",
    "business_signals",
    "capability_states",
    "capacity_checks",
    "carrier_performance",
    "causal_evidence_records",
    "confidence_calibration",
    "connectors",
    "context_edges",
    "context_nodes",
    "contracts",
    "conversation_messages",
    "conversations",
    "counterfactual_records",
    "customer_credits",
    "customers",
    "data_contracts",
    "decision_candidates",
    "decision_overrides",
    "decision_policies",
    "decisions",
    "executive_summaries",
    "external_signal_mappings",
    "financial_baseline_snapshots",
    "financial_intelligence_runs",
    "forecast_points",
    "forecast_runs",
    "fulfillment_allocations",
    "goods_receipt_lines",
    "goods_receipts",
    "ingestion_runs",
    "intelligence_runs",
    "intelligence_snapshots",
    "inventory_intelligence_runs",
    "inventory_positions",
    "inventory_transactions",
    "invoice_lines",
    "invoices",
    "lane_performance",
    "locations",
    "logistics_intelligence_runs",
    "mrp_runs",
    "network_edge_snapshots",
    "network_flow_runs",
    "network_node_snapshots",
    "network_optimization_runs",
    "network_risk_snapshots",
    "onboarding_quarantine",
    "opportunity_findings",
    "optimization_runs",
    "order_lines",
    "orders",
    "outcome_tracking",
    "payments",
    "persistent_alerts",
    "persistent_events",
    "persistent_quarantine",
    "phase14_actions",
    "phase16_cases",
    "phase16_decision_records",
    "phase16_idempotency_keys",
    "phase16_scenario_comparisons",
    "phase16_scenarios",
    "prices",
    "prioritized_actions",
    "process_conformance_results",
    "process_definitions",
    "process_events",
    "process_metric_snapshots",
    "process_object_links",
    "process_sla_rules",
    "process_variants",
    "production_events",
    "products",
    "purchase_order_lines",
    "purchase_order_revisions",
    "purchase_orders",
    "replenishment_policies",
    "replenishment_recommendations",
    "return_requests",
    "returns",
    "risk_findings",
    "sales_order_lines",
    "sales_orders",
    "scenario_assumptions",
    "scenario_metric_snapshots",
    "scenario_results",
    "scenario_runs",
    "scenarios",
    "shadow_evaluations",
    "shipment_evaluations",
    "shipments",
    "studio_agent_versions",
    "studio_agents",
    "studio_audit_logs",
    "studio_deployments",
    "studio_workflow_versions",
    "studio_workflows",
    "supplier_commitments",
    "supplier_financial_document_lines",
    "supplier_financial_documents",
    "supplier_performance",
    "supplier_performances",
    "suppliers",
    "supply_intelligence_runs",
    "value_network_records",
    "work_orders",
]

# Legacy policy tables identified during schema audit.
_LEGACY_POLICY_TABLES = [
    "assurance_findings",
    "assurance_rules",
    "assurance_runs",
    "data_fabric_checkpoints",
    "entity_aliases",
    "schema_drift_logs",
    "source_authority_rules",
]


def _normalize_policy(table_name: str) -> None:
    """Normalize tenant isolation policy to app.tenant_id."""
    bind = op.get_bind()

    bind.execute(
        sa.text(
            f"""
            ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY;
            ALTER TABLE {table_name} FORCE ROW LEVEL SECURITY;

            DROP POLICY IF EXISTS tenant_isolation_policy ON {table_name};
            DROP POLICY IF EXISTS aurix_tenant_isolation ON {table_name};

            CREATE POLICY aurix_tenant_isolation
            ON {table_name}
            USING (
                tenant_id = current_setting('app.tenant_id', true)
            )
            WITH CHECK (
                tenant_id = current_setting('app.tenant_id', true)
            );
            """
        )
    )


def upgrade() -> None:
    if op.get_bind().dialect.name != "postgresql":
        return

    # ------------------------------------------------------------
    # 1. Reconcile connectors with the current ORM contract.
    # ------------------------------------------------------------
    op.add_column(
        "connectors",
        sa.Column(
            "freshness_sla_seconds",
            sa.Float(),
            nullable=False,
            server_default=sa.text("3600.0"),
        ),
    )

    op.add_column(
        "connectors",
        sa.Column(
            "drift_detection_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )

    op.add_column(
        "connectors",
        sa.Column(
            "schema_version",
            sa.String(length=32),
            nullable=False,
            server_default=sa.text("'1.0.0'"),
        ),
    )

    # Remove permanent defaults after backfilling existing rows.
    op.alter_column(
        "connectors",
        "freshness_sla_seconds",
        server_default=None,
    )
    op.alter_column(
        "connectors",
        "drift_detection_enabled",
        server_default=None,
    )
    op.alter_column(
        "connectors",
        "schema_version",
        server_default=None,
    )

    # ------------------------------------------------------------
    # 2. Normalize the seven known legacy policy tables.
    # ------------------------------------------------------------
    for table_name in _LEGACY_POLICY_TABLES:
        _normalize_policy(table_name)

    # ------------------------------------------------------------
    # 3. Normalize tenant-scoped application tables.
    #
    # Users/tenants/auth-control tables are deliberately excluded.
    # Global reference tables without tenant_id are also excluded.
    # ------------------------------------------------------------
    for table_name in _TENANT_RLS_TABLES:
        _normalize_policy(table_name)


def downgrade() -> None:
    if op.get_bind().dialect.name != "postgresql":
        return

    # Remove reconciliation columns.
    op.drop_column("connectors", "schema_version")
    op.drop_column("connectors", "drift_detection_enabled")
    op.drop_column("connectors", "freshness_sla_seconds")

