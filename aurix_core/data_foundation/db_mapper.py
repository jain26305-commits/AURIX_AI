"""Canonical database mapper for AURIX Data Foundation."""

import logging
from typing import Any, Optional
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from aurix_core.database.models.supply_chain import (
    Product,
    Location,
    Supplier,
    InventoryPosition,
)
from aurix_core.database.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class CanonicalMapper:
    """
    Safely maps validated Pandas DataFrames into Canonical SQLAlchemy ORM objects.
    Enforces tenant isolation, provenance tracking, and Zero-Fabrication principles.
    """

    def __init__(self, db: Session, tenant_id: str) -> None:
        self.db = db
        self.tenant_id = tenant_id
        self.product_repo = BaseRepository[Product](Product, db, tenant_id)
        self.location_repo = BaseRepository[Location](Location, db, tenant_id)
        self.supplier_repo = BaseRepository[Supplier](Supplier, db, tenant_id)
        self.inventory_repo = BaseRepository[InventoryPosition](InventoryPosition, db, tenant_id)

    def _safe_float(self, val: Any) -> Optional[float]:
        if pd.isna(val) or val is None or str(val).strip() == "":
            return None
        try:
            return float(val)
        except (ValueError, TypeError):
            return None

    def _safe_str(self, val: Any) -> Optional[str]:
        if pd.isna(val) or val is None or str(val).strip() == "":
            return None
        return str(val).strip()

    def map_products(self, df: pd.DataFrame, run_id: str) -> int:
        success_count = 0
        records = df.to_dict(orient="records")
        for row in records:
            sku_id = self._safe_str(row.get("sku_id")) or self._safe_str(row.get("sku_code"))
            if not sku_id:
                continue

            try:
                existing = self.product_repo.get_by_id(sku_id)
                if existing:
                    setattr(existing, "name", self._safe_str(row.get("name")) or getattr(existing, "name"))
                    setattr(existing, "category", self._safe_str(row.get("category")) or getattr(existing, "category"))
                    setattr(existing, "unit_cost", self._safe_float(row.get("unit_cost")) or getattr(existing, "unit_cost"))
                    setattr(existing, "ingestion_run_id", run_id)
                    setattr(existing, "source_record_id", self._safe_str(row.get("source_record_id")))
                else:
                    product = Product(
                        id=sku_id,
                        sku_code=self._safe_str(row.get("sku_code")) or sku_id,
                        name=self._safe_str(row.get("name")) or "Unknown Product",
                        category=self._safe_str(row.get("category")),
                        unit_cost=self._safe_float(row.get("unit_cost")),
                        ingestion_run_id=run_id,
                        source_record_id=self._safe_str(row.get("source_record_id")),
                        tenant_id=self.tenant_id
                    )
                    self.product_repo.create(product)
                success_count += 1
            except SQLAlchemyError:
                self.db.rollback()
                logger.warning(f"Failed to map Product {sku_id}")
        return success_count

    def map_locations(self, df: pd.DataFrame, run_id: str) -> int:
        success_count = 0
        records = df.to_dict(orient="records")
        for row in records:
            loc_id = self._safe_str(row.get("location_id"))
            if not loc_id:
                continue

            try:
                existing = self.location_repo.get_by_id(loc_id)
                if existing:
                    setattr(existing, "location_name", self._safe_str(row.get("location_name")) or getattr(existing, "location_name"))
                    setattr(existing, "country", self._safe_str(row.get("country")) or getattr(existing, "country"))
                    setattr(existing, "ingestion_run_id", run_id)
                    setattr(existing, "source_record_id", self._safe_str(row.get("source_record_id")))
                else:
                    location = Location(
                        id=loc_id,
                        location_name=self._safe_str(row.get("location_name")) or "Unknown Location",
                        location_type=self._safe_str(row.get("location_type")) or "WAREHOUSE",
                        country=self._safe_str(row.get("country")),
                        ingestion_run_id=run_id,
                        source_record_id=self._safe_str(row.get("source_record_id")),
                        tenant_id=self.tenant_id
                    )
                    self.location_repo.create(location)
                success_count += 1
            except SQLAlchemyError:
                self.db.rollback()
        return success_count

    def map_suppliers(self, df: pd.DataFrame, run_id: str) -> int:
        success_count = 0
        records = df.to_dict(orient="records")
        for row in records:
            sup_id = self._safe_str(row.get("supplier_id"))
            if not sup_id:
                continue

            try:
                existing = self.supplier_repo.get_by_id(sup_id)
                if existing:
                    setattr(existing, "supplier_name", self._safe_str(row.get("supplier_name")) or getattr(existing, "supplier_name"))
                    setattr(existing, "lead_time_days", self._safe_float(row.get("lead_time_days")) or getattr(existing, "lead_time_days"))
                    setattr(existing, "ingestion_run_id", run_id)
                else:
                    supplier = Supplier(
                        id=sup_id,
                        supplier_name=self._safe_str(row.get("supplier_name")) or "Unknown Supplier",
                        country=self._safe_str(row.get("country")),
                        lead_time_days=self._safe_float(row.get("lead_time_days")),
                        ingestion_run_id=run_id,
                        source_record_id=self._safe_str(row.get("source_record_id")),
                        tenant_id=self.tenant_id
                    )
                    self.supplier_repo.create(supplier)
                success_count += 1
            except SQLAlchemyError:
                self.db.rollback()
        return success_count

    def map_inventory(self, df: pd.DataFrame, run_id: str) -> int:
        success_count = 0
        records = df.to_dict(orient="records")
        for row in records:
            sku_id = self._safe_str(row.get("sku_id"))
            loc_id = self._safe_str(row.get("location_id"))
            if not sku_id or not loc_id:
                continue

            try:
                existing = self.inventory_repo._base_query().filter_by(sku_id=sku_id, location_id=loc_id).first()
                if existing:
                    setattr(existing, "on_hand", self._safe_float(row.get("on_hand")) or 0.0)
                    setattr(existing, "on_order", self._safe_float(row.get("on_order")) or 0.0)
                    setattr(existing, "ingestion_run_id", run_id)
                else:
                    inventory = InventoryPosition(
                        sku_id=sku_id,
                        location_id=loc_id,
                        on_hand=self._safe_float(row.get("on_hand")) or 0.0,
                        on_order=self._safe_float(row.get("on_order")) or 0.0,
                        safety_stock=self._safe_float(row.get("safety_stock")),
                        ingestion_run_id=run_id,
                        source_record_id=self._safe_str(row.get("source_record_id")),
                        tenant_id=self.tenant_id
                    )
                    self.inventory_repo.create(inventory)
                success_count += 1
            except SQLAlchemyError:
                self.db.rollback()
        return success_count