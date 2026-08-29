"""Add durable onboarding staging for resumable tenant-scoped uploads.

Revision ID: 0023_phase33_onboarding_staging
Revises: 0022_phase32_phase21_23_rls_cleanup
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "0023_phase33_onboarding_staging"
down_revision: Union[str, None] = "0022_phase32_phase21_23_rls_cleanup"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    if op.get_bind().dialect.name != "postgresql":
        return

    op.create_table(
        "onboarding_datasets",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False, index=True),
        sa.Column("source_name", sa.String(length=255), nullable=False),
        sa.Column("source_type", sa.String(length=32), nullable=False),
        sa.Column("input_hash", sa.String(length=128), nullable=False, index=True),
        sa.Column("raw_payload_json", sa.Text(), nullable=False),
        sa.Column("source_columns_json", sa.Text(), nullable=True),
        sa.Column("detected_entity", sa.String(length=128), nullable=True, index=True),
        sa.Column("status", sa.String(length=32), nullable=False, default="RECEIVED"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    op.execute(
        """
        ALTER TABLE onboarding_datasets
        ENABLE ROW LEVEL SECURITY;

        ALTER TABLE onboarding_datasets
        FORCE ROW LEVEL SECURITY;

        DROP POLICY IF EXISTS aurix_tenant_isolation
        ON onboarding_datasets;

        CREATE POLICY aurix_tenant_isolation
        ON onboarding_datasets
        USING (
            tenant_id = current_setting('app.tenant_id', true)
        )
        WITH CHECK (
            tenant_id = current_setting('app.tenant_id', true)
        );
        """
    )


def downgrade() -> None:
    if op.get_bind().dialect.name != "postgresql":
        return

    op.execute(
        """
        DROP POLICY IF EXISTS aurix_tenant_isolation
        ON onboarding_datasets;

        ALTER TABLE onboarding_datasets
        NO FORCE ROW LEVEL SECURITY;

        ALTER TABLE onboarding_datasets
        DISABLE ROW LEVEL SECURITY;
        """
    )

    op.drop_table("onboarding_datasets")
