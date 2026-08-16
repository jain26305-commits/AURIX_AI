"""Unit and adversarial test suite for AURIX database foundation and tenant isolation."""

import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.exc import IntegrityError

from aurix_core.database.engine import Base
from aurix_core.database.models.supply_chain import (
    InventoryPosition,
    Location,
    Product,
    Supplier,
)
from aurix_core.database.repositories.base import BaseRepository


class TestDatabaseFoundation(unittest.TestCase):
    """Test suite verifying database creation, CRUD operations, and multi-tenant data isolation."""

    def setUp(self) -> None:
        """Sets up an isolated, in-memory SQLite database for each test case."""
        self.engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine, autocommit=False, autoflush=False)
        self.db: Session = self.SessionLocal()

    def tearDown(self) -> None:
        """Closes the session and drops the in-memory schema after each test case."""
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)

    def test_01_tenant_isolation_product_repository(self) -> None:
        """Adversarial test: Verifies Tenant A cannot access or query Tenant B's products."""
        repo_a = BaseRepository[Product](Product, self.db, tenant_id="tenant_alpha")
        repo_b = BaseRepository[Product](Product, self.db, tenant_id="tenant_beta")

        prod_a = Product(id="P1", sku_code="SKU-A", name="Widget A", tenant_id="tenant_alpha")
        prod_b = Product(id="P2", sku_code="SKU-B", name="Widget B", tenant_id="tenant_beta")

        repo_a.create(prod_a)
        repo_b.create(prod_b)

        # Query as Tenant Alpha
        alpha_products = repo_a.list_all()
        self.assertEqual(len(alpha_products), 1)
        self.assertEqual(alpha_products[0].id, "P1")
        self.assertEqual(alpha_products[0].tenant_id, "tenant_alpha")

        # Query as Tenant Beta
        beta_products = repo_b.list_all()
        self.assertEqual(len(beta_products), 1)
        self.assertEqual(beta_products[0].id, "P2")
        self.assertEqual(beta_products[0].tenant_id, "tenant_beta")

        # Cross-tenant get_by_id attempts MUST return None
        self.assertIsNone(repo_a.get_by_id("P2"))
        self.assertIsNone(repo_b.get_by_id("P1"))

        # Cross-tenant delete attempt MUST fail
        deleted = repo_a.delete("P2")
        self.assertFalse(deleted)
        self.assertIsNotNone(repo_b.get_by_id("P2"))

    def test_02_crud_operations_location(self) -> None:
        """Tests full CRUD lifecycle for Location canonical entity."""
        repo = BaseRepository[Location](Location, self.db, tenant_id="tenant_test")
        loc = Location(id="LOC-1", location_name="Main DC", location_type="DC", tenant_id="tenant_test")

        # Create
        created = repo.create(loc)
        self.assertEqual(created.id, "LOC-1")

        # Read
        retrieved = repo.get_by_id("LOC-1")
        self.assertIsNotNone(retrieved)
        if retrieved:
            self.assertEqual(retrieved.location_name, "Main DC")

        # Delete
        deleted = repo.delete("LOC-1")
        self.assertTrue(deleted)
        self.assertIsNone(repo.get_by_id("LOC-1"))

    def test_03_inventory_position_and_foreign_keys(self) -> None:
        """Tests InventoryPosition persistence referencing Product and Location."""
        p_repo = BaseRepository[Product](Product, self.db, tenant_id="tenant_test")
        l_repo = BaseRepository[Location](Location, self.db, tenant_id="tenant_test")
        i_repo = BaseRepository[InventoryPosition](InventoryPosition, self.db, tenant_id="tenant_test")

        p_repo.create(Product(id="P100", sku_code="SKU-100", name="Item 100", tenant_id="tenant_test"))
        l_repo.create(Location(id="L100", location_name="DC 100", location_type="DC", tenant_id="tenant_test"))

        inv = InventoryPosition(
            sku_id="P100",
            location_id="L100",
            on_hand=150.0,
            on_order=50.0,
            tenant_id="tenant_test",
        )
        created_inv = i_repo.create(inv)
        self.assertIsNotNone(created_inv.id)
        self.assertEqual(created_inv.on_hand, 150.0)

    def test_04_idempotent_schema_creation(self) -> None:
        """Verifies running create_all multiple times does not corrupt or wipe data."""
        Base.metadata.create_all(bind=self.engine)
        repo = BaseRepository[Supplier](Supplier, self.db, tenant_id="tenant_test")
        repo.create(Supplier(id="SUP-1", supplier_name="Vendor One", tenant_id="tenant_test"))

        # Re-trigger schema creation
        Base.metadata.create_all(bind=self.engine)
        self.assertIsNotNone(repo.get_by_id("SUP-1"))

    def test_05_transaction_rollback_on_duplicate(self) -> None:
        """Verifies that inserting a duplicate primary key fails safely and can be rolled back."""
        repo = BaseRepository[Product](Product, self.db, tenant_id="tenant_test")

        prod1 = Product(id="DUP-1", sku_code="SKU-DUP", name="Widget Dup", tenant_id="tenant_test")
        repo.create(prod1)

        prod2 = Product(id="DUP-1", sku_code="SKU-DUP-2", name="Widget Dup 2", tenant_id="tenant_test")

        with self.assertRaises(IntegrityError):
            repo.create(prod2)

        self.db.rollback()

        # Verify the session is still usable after rollback
        valid_prod = Product(id="VALID-1", sku_code="SKU-VAL", name="Widget Valid", tenant_id="tenant_test")
        repo.create(valid_prod)
        self.assertIsNotNone(repo.get_by_id("VALID-1"))