"""Harden Phase 16 collaboration, matching, idempotency, and decision audit.

Revision ID: 0005_phase16_operational_hardening
Revises: 0004_phase16_operational_lifecycle
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0005_phase16_operational_hardening"
down_revision: Union[str, None] = "0004_phase16_operational_lifecycle"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_TABLES = [
    "purchase_order_revisions",
    "supplier_commitments",
    "advance_shipment_notices",
    "advance_shipment_notice_lines",
    "supplier_financial_document_lines",
    "phase16_idempotency_keys",
    "phase16_scenario_comparisons",
    "phase16_decision_records",
]


def _json_type() -> sa.types.TypeEngine:
    """Return JSONB on PostgreSQL and fallback JSON on other dialects."""
    return sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def _apply_rls() -> None:
    if op.get_bind().dialect.name != "postgresql":
        return
    for table_name in _TABLES:
        op.execute(
            sa.text(
                f"""
                ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY;
                ALTER TABLE {table_name} FORCE ROW LEVEL SECURITY;
                DROP POLICY IF EXISTS aurix_tenant_isolation ON {table_name};
                CREATE POLICY aurix_tenant_isolation ON {table_name}
                USING (tenant_id = current_setting('app.tenant_id', true))
                WITH CHECK (tenant_id = current_setting('app.tenant_id', true));
                """
            )
        )


def _remove_rls() -> None:
    if op.get_bind().dialect.name != "postgresql":
        return
    for table_name in reversed(_TABLES):
        op.execute(
            sa.text(
                f"""
                DROP POLICY IF EXISTS aurix_tenant_isolation ON {table_name};
                ALTER TABLE {table_name} NO FORCE ROW LEVEL SECURITY;
                ALTER TABLE {table_name} DISABLE ROW LEVEL SECURITY;
                """
            )
        )


def upgrade() -> None:
    json_col = _json_type()

    op.add_column("purchase_orders", sa.Column("supplier_reference", sa.String(length=128), nullable=True))
    op.add_column("purchase_orders", sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("purchase_orders", sa.Column("committed_date", sa.DateTime(timezone=True), nullable=True))
    op.add_column("purchase_orders", sa.Column("cancelled_reason", sa.Text(), nullable=True))

    op.add_column("supplier_financial_documents", sa.Column("reference_document_id", sa.String(length=64), nullable=True))

    op.create_table(
        "purchase_order_revisions",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("purchase_order_id", sa.String(length=64), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("snapshot_json", json_col, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "purchase_order_id", "revision", name="uq_phase16_po_revision"),
    )
    op.create_index("ix_purchase_order_revisions_tenant_id", "purchase_order_revisions", ["tenant_id"])
    op.create_index("ix_purchase_order_revisions_po_id", "purchase_order_revisions", ["purchase_order_id"])

    op.create_table(
        "supplier_commitments",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("purchase_order_id", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("committed_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("committed_quantity", sa.Numeric(precision=14, scale=4), nullable=True),
        sa.Column("alternative_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("supplier_reference", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_supplier_commitments_tenant_id", "supplier_commitments", ["tenant_id"])
    op.create_index("ix_supplier_commitments_po_id", "supplier_commitments", ["purchase_order_id"])
    op.create_index("ix_supplier_commitments_status", "supplier_commitments", ["tenant_id", "status"])

    op.create_table(
        "advance_shipment_notices",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("purchase_order_id", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("expected_arrival_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("carrier", sa.String(length=128), nullable=True),
        sa.Column("tracking_number", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_advance_shipment_notices_tenant_id", "advance_shipment_notices", ["tenant_id"])
    op.create_index("ix_advance_shipment_notices_po_id", "advance_shipment_notices", ["purchase_order_id"])

    op.create_table(
        "advance_shipment_notice_lines",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("asn_id", sa.String(length=64), nullable=False),
        sa.Column("purchase_order_line_id", sa.String(length=64), nullable=False),
        sa.Column("shipped_quantity", sa.Numeric(precision=14, scale=4), nullable=False),
    )
    op.create_index("ix_asn_lines_tenant_id", "advance_shipment_notice_lines", ["tenant_id"])
    op.create_index("ix_asn_lines_asn_id", "advance_shipment_notice_lines", ["asn_id"])
    op.create_index("ix_asn_lines_po_line_id", "advance_shipment_notice_lines", ["purchase_order_line_id"])

    op.create_table(
        "supplier_financial_document_lines",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("financial_document_id", sa.String(length=64), nullable=False),
        sa.Column("purchase_order_line_id", sa.String(length=64), nullable=False),
        sa.Column("quantity", sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column("unit_price", sa.Numeric(precision=14, scale=4), nullable=True),
        sa.Column("tax_amount", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("freight_amount", sa.Numeric(precision=14, scale=2), nullable=False),
    )
    op.create_index("ix_fin_doc_lines_tenant_id", "supplier_financial_document_lines", ["tenant_id"])
    op.create_index("ix_fin_doc_lines_document_id", "supplier_financial_document_lines", ["financial_document_id"])
    op.create_index("ix_fin_doc_lines_po_line_id", "supplier_financial_document_lines", ["purchase_order_line_id"])

    op.create_table(
        "phase16_idempotency_keys",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("idempotency_key", sa.String(length=255), nullable=False),
        sa.Column("operation", sa.String(length=128), nullable=False),
        sa.Column("source_system", sa.String(length=64), nullable=False),
        sa.Column("external_record_id", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("result_json", json_col, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("tenant_id", "idempotency_key", name="uq_phase16_idempotency_tenant_key"),
    )
    op.create_index("ix_phase16_idempotency_operation", "phase16_idempotency_keys", ["tenant_id", "operation"])

    op.create_table(
        "phase16_scenario_comparisons",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("scenario_ids_json", json_col, nullable=False),
        sa.Column("comparison_json", json_col, nullable=False),
        sa.Column("recommended_scenario_id", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_phase16_scenario_comparisons_tenant_id", "phase16_scenario_comparisons", ["tenant_id"])

    op.create_table(
        "phase16_decision_records",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("case_id", sa.String(length=64), nullable=True),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("answer_source", sa.String(length=64), nullable=False),
        sa.Column("ai_provider", sa.String(length=64), nullable=True),
        sa.Column("fact_pack_id", sa.String(length=128), nullable=True),
        sa.Column("tool_calls_json", json_col, nullable=False),
        sa.Column("recommendation_json", json_col, nullable=False),
        sa.Column("provenance_json", json_col, nullable=False),
        sa.Column("outcome_json", json_col, nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_phase16_decision_records_tenant_id", "phase16_decision_records", ["tenant_id"])
    op.create_index("ix_phase16_decision_records_case_id", "phase16_decision_records", ["tenant_id", "case_id"])

    _apply_rls()


def downgrade() -> None:
    _remove_rls()

    # Remove columns added to Phase 16 baseline tables before dropping them.
    op.drop_column("supplier_financial_documents", "reference_document_id")
    op.drop_column("purchase_orders", "cancelled_reason")
    op.drop_column("purchase_orders", "committed_date")
    op.drop_column("purchase_orders", "acknowledged_at")
    op.drop_column("purchase_orders", "supplier_reference")

    for table_name in reversed(_TABLES):
        op.drop_table(table_name)
