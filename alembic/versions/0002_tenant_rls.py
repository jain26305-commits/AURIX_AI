"""Enable PostgreSQL RLS for every application table carrying tenant_id.

Revision ID: 0002_tenant_rls
Revises: 0001_initial_aurix_schema
"""

from typing import Sequence, Union

from alembic import op

revision: str = "0002_tenant_rls"
down_revision: Union[str, None] = "0001_initial_aurix_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Enable tenant-scoped RLS on PostgreSQL; no-op on SQLite."""
    if op.get_bind().dialect.name != "postgresql":
        return

    op.execute(
        """
        DO $$
        DECLARE
            table_record RECORD;
        BEGIN
            FOR table_record IN
                SELECT DISTINCT table_schema, table_name
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND column_name = 'tenant_id'
            LOOP
                EXECUTE format(
                    'ALTER TABLE %I.%I ENABLE ROW LEVEL SECURITY',
                    table_record.table_schema,
                    table_record.table_name
                );

                EXECUTE format(
                    'ALTER TABLE %I.%I FORCE ROW LEVEL SECURITY',
                    table_record.table_schema,
                    table_record.table_name
                );

                EXECUTE format(
                    'DROP POLICY IF EXISTS aurix_tenant_isolation ON %I.%I',
                    table_record.table_schema,
                    table_record.table_name
                );

                EXECUTE format(
                    'CREATE POLICY aurix_tenant_isolation '
                    'ON %I.%I '
                    'USING (tenant_id = current_setting(''app.tenant_id'', true)) '
                    'WITH CHECK (tenant_id = current_setting(''app.tenant_id'', true))',
                    table_record.table_schema,
                    table_record.table_name
                );
            END LOOP;
        END $$;
        """
    )


def downgrade() -> None:
    """Remove AURIX tenant RLS policies and enforcement on PostgreSQL."""
    if op.get_bind().dialect.name != "postgresql":
        return

    op.execute(
        """
        DO $$
        DECLARE
            table_record RECORD;
        BEGIN
            FOR table_record IN
                SELECT DISTINCT table_schema, table_name
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND column_name = 'tenant_id'
            LOOP
                EXECUTE format(
                    'DROP POLICY IF EXISTS aurix_tenant_isolation ON %I.%I',
                    table_record.table_schema,
                    table_record.table_name
                );

                EXECUTE format(
                    'ALTER TABLE %I.%I NO FORCE ROW LEVEL SECURITY',
                    table_record.table_schema,
                    table_record.table_name
                );

                EXECUTE format(
                    'ALTER TABLE %I.%I DISABLE ROW LEVEL SECURITY',
                    table_record.table_schema,
                    table_record.table_name
                );
            END LOOP;
        END $$;
        """
    )