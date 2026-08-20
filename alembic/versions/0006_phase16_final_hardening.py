"""Final Phase 16 provenance, case, and external-identity hardening.

Revision ID: 0006_phase16_final_hardening
Revises: 0005_phase16_operational_hardening
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0006_phase16_final_hardening"
down_revision: Union[str, None] = "0005_phase16_operational_hardening"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _json_type() -> sa.types.TypeEngine:
    """Return JSONB on PostgreSQL and fallback JSON on other dialects."""
    return sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def _add_column_if_missing(table: str, column: sa.Column) -> None:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        inspector = sa.inspect(bind)
        existing = {col["name"] for col in inspector.get_columns(table)}
        if column.name in existing:
            return
    op.add_column(table, column)


def upgrade() -> None:
    json_col = _json_type()

    _add_column_if_missing(
        "phase16_idempotency_keys",
        sa.Column("source_identity", sa.String(length=320), nullable=True),
    )
    _add_column_if_missing(
        "phase16_cases",
        sa.Column("owner", sa.String(length=128), nullable=True),
    )
    _add_column_if_missing(
        "phase16_cases",
        sa.Column("priority", sa.String(length=32), nullable=True),
    )
    _add_column_if_missing(
        "phase16_cases",
        sa.Column("sla_due_at", sa.DateTime(timezone=True), nullable=True),
    )
    _add_column_if_missing(
        "phase16_cases",
        sa.Column("resolution_json", json_col, nullable=True),
    )
    _add_column_if_missing(
        "phase16_decision_records",
        sa.Column("model_used", sa.String(length=128), nullable=True),
    )
    _add_column_if_missing(
        "phase16_decision_records",
        sa.Column("expected_outcome_json", json_col, nullable=True),
    )
    _add_column_if_missing(
        "phase16_decision_records",
        sa.Column("actual_outcome_json", json_col, nullable=True),
    )
    _add_column_if_missing(
        "phase16_decision_records",
        sa.Column("approval_id", sa.String(length=64), nullable=True),
    )
    _add_column_if_missing(
        "phase16_decision_records",
        sa.Column("action_id", sa.String(length=64), nullable=True),
    )
    _add_column_if_missing(
        "phase16_decision_records",
        sa.Column("value_realized", sa.Numeric(precision=14, scale=2), nullable=True),
    )

    # External source identity must be unique within a tenant. Multiple NULLs are allowed.
    op.create_index(
        "uq_phase16_idempotency_source_identity",
        "phase16_idempotency_keys",
        ["tenant_id", "source_identity"],
        unique=True,
    )

    # Re-apply tenant RLS to the modified Phase 16 tables on PostgreSQL only.
    if op.get_bind().dialect.name == "postgresql":
        for table_name in ("phase16_idempotency_keys", "phase16_cases", "phase16_decision_records"):
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


def downgrade() -> None:
    if op.get_bind().dialect.name == "postgresql":
        for table_name in ("phase16_decision_records", "phase16_cases", "phase16_idempotency_keys"):
            op.execute(
                sa.text(
                    f"""
                    DROP POLICY IF EXISTS aurix_tenant_isolation ON {table_name};
                    ALTER TABLE {table_name} NO FORCE ROW LEVEL SECURITY;
                    ALTER TABLE {table_name} DISABLE ROW LEVEL SECURITY;
                    """
                )
            )
    op.drop_index("uq_phase16_idempotency_source_identity", table_name="phase16_idempotency_keys")
    for table_name, column in (
        ("phase16_decision_records", "value_realized"),
        ("phase16_decision_records", "action_id"),
        ("phase16_decision_records", "approval_id"),
        ("phase16_decision_records", "actual_outcome_json"),
        ("phase16_decision_records", "expected_outcome_json"),
        ("phase16_decision_records", "model_used"),
        ("phase16_cases", "resolution_json"),
        ("phase16_cases", "sla_due_at"),
        ("phase16_cases", "priority"),
        ("phase16_cases", "owner"),
        ("phase16_idempotency_keys", "source_identity"),
    ):
        op.drop_column(table_name, column)