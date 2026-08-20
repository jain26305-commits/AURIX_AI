"""Phase 16 procurement, planning, fulfillment and returns schema.

Revision ID: 0004_phase16_operational_lifecycle
Revises: 0003_onboarding_quarantine
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0004_phase16_operational_lifecycle"
down_revision: Union[str, None] = "0003_onboarding_quarantine"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_PHASE16_TABLES = [
    "purchase_orders",
    "purchase_order_lines",
    "goods_receipts",
    "goods_receipt_lines",
    "supplier_financial_documents",
    "return_requests",
    "bom_headers",
    "bom_lines",
    "mrp_runs",
    "capacity_checks",
    "sales_orders",
    "sales_order_lines",
    "fulfillment_allocations",
    "phase16_scenarios",
    "phase16_cases",
]


def _json_type() -> sa.types.TypeEngine:
    """Return JSONB on PostgreSQL and fallback JSON on other dialects."""
    return sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def _apply_postgres_rls() -> None:
    if op.get_bind().dialect.name != "postgresql":
        return

    for table_name in _PHASE16_TABLES:
        op.execute(
            sa.text(
                f"""
                ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY;
                ALTER TABLE {table_name} FORCE ROW LEVEL SECURITY;
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


def _remove_postgres_rls() -> None:
    if op.get_bind().dialect.name != "postgresql":
        return

    for table_name in reversed(_PHASE16_TABLES):
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
    """Apply Phase 16 procurement, planning, fulfillment and returns schema."""
    bind = op.get_bind()

    # Alembic's default version_num column can be only VARCHAR(32).
    # Phase 16 revision identifiers exceed that length, so widen the
    # PostgreSQL version column before Alembic records revision 0004.
    if bind.dialect.name == "postgresql":
        op.execute(
            """
            ALTER TABLE alembic_version
            ALTER COLUMN version_num TYPE VARCHAR(128)
            """
        )

    json_col = _json_type()

    op.create_table(
        "purchase_orders",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("supplier_id", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("required_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_request_id", sa.String(length=128), nullable=True),
        sa.Column("revision", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("total_amount", sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column("currency", sa.String(length=16), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_purchase_orders_tenant_id", "purchase_orders", ["tenant_id"])
    op.create_index("ix_purchase_orders_supplier_id", "purchase_orders", ["supplier_id"])
    op.create_index(
        "ix_phase16_po_tenant_supplier_status",
        "purchase_orders",
        ["tenant_id", "supplier_id", "status"],
    )

    op.create_table(
        "purchase_order_lines",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("purchase_order_id", sa.String(length=64), nullable=False),
        sa.Column("sku_id", sa.String(length=64), nullable=False),
        sa.Column("quantity", sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column(
            "received_quantity",
            sa.Numeric(precision=14, scale=4),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "accepted_quantity",
            sa.Numeric(precision=14, scale=4),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "rejected_quantity",
            sa.Numeric(precision=14, scale=4),
            nullable=False,
            server_default="0",
        ),
        sa.Column("unit_price", sa.Numeric(precision=14, scale=4), nullable=True),
        sa.Column("currency", sa.String(length=16), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    for name, cols in [
        ("ix_purchase_order_lines_tenant_id", ["tenant_id"]),
        ("ix_purchase_order_lines_purchase_order_id", ["purchase_order_id"]),
        ("ix_purchase_order_lines_sku_id", ["sku_id"]),
        ("ix_phase16_po_line_tenant_po_sku", ["tenant_id", "purchase_order_id", "sku_id"]),
    ]:
        op.create_index(name, "purchase_order_lines", cols)

    op.create_table(
        "goods_receipts",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("purchase_order_id", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_goods_receipts_tenant_id", "goods_receipts", ["tenant_id"])
    op.create_index("ix_goods_receipts_purchase_order_id", "goods_receipts", ["purchase_order_id"])

    op.create_table(
        "goods_receipt_lines",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("goods_receipt_id", sa.String(length=64), nullable=False),
        sa.Column("purchase_order_line_id", sa.String(length=64), nullable=False),
        sa.Column("received_quantity", sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column("accepted_quantity", sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column("rejected_quantity", sa.Numeric(precision=14, scale=4), nullable=False),
    )
    for name, cols in [
        ("ix_goods_receipt_lines_tenant_id", ["tenant_id"]),
        ("ix_goods_receipt_lines_receipt_id", ["goods_receipt_id"]),
        ("ix_goods_receipt_lines_po_line_id", ["purchase_order_line_id"]),
    ]:
        op.create_index(name, "goods_receipt_lines", cols)

    op.create_table(
        "supplier_financial_documents",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("purchase_order_id", sa.String(length=64), nullable=False),
        sa.Column("document_type", sa.String(length=32), nullable=False),
        sa.Column("document_number", sa.String(length=128), nullable=False),
        sa.Column("amount", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=16), nullable=False),
        sa.Column("matched_receipt_id", sa.String(length=64), nullable=True),
        sa.Column("match_status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    for name, cols in [
        ("ix_supplier_financial_documents_tenant_id", ["tenant_id"]),
        ("ix_supplier_financial_documents_po_id", ["purchase_order_id"]),
        ("ix_supplier_financial_documents_doc_number", ["document_number"]),
    ]:
        op.create_index(name, "supplier_financial_documents", cols)

    op.create_table(
        "return_requests",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("source_order_id", sa.String(length=64), nullable=True),
        sa.Column("sku_id", sa.String(length=64), nullable=False),
        sa.Column("quantity", sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("disposition", sa.String(length=32), nullable=True),
        sa.Column("recovery_value", sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    for name, cols in [
        ("ix_return_requests_tenant_id", ["tenant_id"]),
        ("ix_return_requests_source_order_id", ["source_order_id"]),
        ("ix_return_requests_sku_id", ["sku_id"]),
        ("ix_return_requests_status", ["status"]),
    ]:
        op.create_index(name, "return_requests", cols)

    op.create_table(
        "bom_headers",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("parent_sku_id", sa.String(length=64), nullable=False),
        sa.Column("version", sa.String(length=64), nullable=False),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    for name, cols in [
        ("ix_bom_headers_tenant_id", ["tenant_id"]),
        ("ix_bom_headers_parent_sku_id", ["parent_sku_id"]),
    ]:
        op.create_index(name, "bom_headers", cols)

    op.create_table(
        "bom_lines",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("bom_id", sa.String(length=64), nullable=False),
        sa.Column("component_sku_id", sa.String(length=64), nullable=False),
        sa.Column("quantity_per", sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column("scrap_pct", sa.Numeric(precision=6, scale=4), nullable=False, server_default="0"),
    )
    for name, cols in [
        ("ix_bom_lines_tenant_id", ["tenant_id"]),
        ("ix_bom_lines_bom_id", ["bom_id"]),
        ("ix_bom_lines_component_sku_id", ["component_sku_id"]),
    ]:
        op.create_index(name, "bom_lines", cols)

    op.create_table(
        "mrp_runs",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("requirements_json", json_col, nullable=False),
        sa.Column("results_json", json_col, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_mrp_runs_tenant_id", "mrp_runs", ["tenant_id"])

    op.create_table(
        "capacity_checks",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("results_json", json_col, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_capacity_checks_tenant_id", "capacity_checks", ["tenant_id"])

    op.create_table(
        "sales_orders",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("customer_id", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("requested_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    for name, cols in [
        ("ix_sales_orders_tenant_id", ["tenant_id"]),
        ("ix_sales_orders_customer_id", ["customer_id"]),
        ("ix_sales_orders_status", ["status"]),
    ]:
        op.create_index(name, "sales_orders", cols)

    op.create_table(
        "sales_order_lines",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("sales_order_id", sa.String(length=64), nullable=False),
        sa.Column("sku_id", sa.String(length=64), nullable=False),
        sa.Column("quantity", sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column(
            "allocated_quantity",
            sa.Numeric(precision=14, scale=4),
            nullable=False,
            server_default="0",
        ),
        sa.Column("location_id", sa.String(length=64), nullable=True),
    )
    for name, cols in [
        ("ix_sales_order_lines_tenant_id", ["tenant_id"]),
        ("ix_sales_order_lines_order_id", ["sales_order_id"]),
        ("ix_sales_order_lines_sku_id", ["sku_id"]),
    ]:
        op.create_index(name, "sales_order_lines", cols)

    op.create_table(
        "fulfillment_allocations",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("sales_order_line_id", sa.String(length=64), nullable=False),
        sa.Column("sku_id", sa.String(length=64), nullable=False),
        sa.Column("quantity", sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    for name, cols in [
        ("ix_fulfillment_allocations_tenant_id", ["tenant_id"]),
        ("ix_fulfillment_allocations_line_id", ["sales_order_line_id"]),
        ("ix_fulfillment_allocations_sku_id", ["sku_id"]),
    ]:
        op.create_index(name, "fulfillment_allocations", cols)

    op.create_table(
        "phase16_scenarios",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("scenario_type", sa.String(length=64), nullable=False),
        sa.Column("parameters_json", json_col, nullable=False),
        sa.Column("result_json", json_col, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    for name, cols in [
        ("ix_phase16_scenarios_tenant_id", ["tenant_id"]),
        ("ix_phase16_scenarios_type", ["scenario_type"]),
    ]:
        op.create_index(name, "phase16_scenarios", cols)

    op.create_table(
        "phase16_cases",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("case_type", sa.String(length=64), nullable=False),
        sa.Column("severity", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("impact_json", json_col, nullable=True),
        sa.Column("recommended_action_json", json_col, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    for name, cols in [
        ("ix_phase16_cases_tenant_id", ["tenant_id"]),
        ("ix_phase16_cases_type", ["case_type"]),
        ("ix_phase16_cases_status", ["status"]),
    ]:
        op.create_index(name, "phase16_cases", cols)

    _apply_postgres_rls()


def downgrade() -> None:
    """Remove Phase 16 procurement, planning, fulfillment and returns schema."""
    _remove_postgres_rls()

    tables = [
        "phase16_cases",
        "phase16_scenarios",
        "fulfillment_allocations",
        "sales_order_lines",
        "sales_orders",
        "capacity_checks",
        "mrp_runs",
        "bom_lines",
        "bom_headers",
        "return_requests",
        "supplier_financial_documents",
        "goods_receipt_lines",
        "goods_receipts",
        "purchase_order_lines",
        "purchase_orders",
    ]

    for table_name in tables:
        op.drop_table(table_name)