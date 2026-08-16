"""Persist rejected onboarding rows for safe review and audit.

Revision ID: 0003_onboarding_quarantine
Revises: 0002_tenant_rls
"""

from alembic import op
import sqlalchemy as sa

revision = "0003_onboarding_quarantine"
down_revision = "0002_tenant_rls"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "onboarding_quarantine",
        sa.Column("id", sa.String(length=64), primary_key=True, nullable=False),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("run_id", sa.String(length=64), nullable=False),
        sa.Column("row_hash", sa.String(length=128), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_onboarding_quarantine_id", "onboarding_quarantine", ["id"])
    op.create_index("ix_onboarding_quarantine_tenant_id", "onboarding_quarantine", ["tenant_id"])
    op.create_index("ix_onboarding_quarantine_run_id", "onboarding_quarantine", ["run_id"])
    op.create_index("ix_onboarding_quarantine_row_hash", "onboarding_quarantine", ["row_hash"])

    # Apply the same tenant RLS policy as every other tenant-owned table.
    op.execute("""
        ALTER TABLE onboarding_quarantine ENABLE ROW LEVEL SECURITY;
        ALTER TABLE onboarding_quarantine FORCE ROW LEVEL SECURITY;
        CREATE POLICY aurix_tenant_isolation
        ON onboarding_quarantine
        USING (tenant_id = current_setting('app.tenant_id', true))
        WITH CHECK (tenant_id = current_setting('app.tenant_id', true));
    """)


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS aurix_tenant_isolation ON onboarding_quarantine")
    op.execute("ALTER TABLE onboarding_quarantine NO FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE onboarding_quarantine DISABLE ROW LEVEL SECURITY")
    op.drop_index("ix_onboarding_quarantine_row_hash", table_name="onboarding_quarantine")
    op.drop_index("ix_onboarding_quarantine_run_id", table_name="onboarding_quarantine")
    op.drop_index("ix_onboarding_quarantine_tenant_id", table_name="onboarding_quarantine")
    op.drop_index("ix_onboarding_quarantine_id", table_name="onboarding_quarantine")
    op.drop_table("onboarding_quarantine")
