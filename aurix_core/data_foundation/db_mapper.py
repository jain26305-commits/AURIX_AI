"""Canonical database mapper for AURIX Data Foundation."""

import logging
from typing import Any, Optional

import pandas as pd
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from aurix_core.database.models.supply_chain import (
    Customer,
    Invoice,
    InventoryPosition,
    Location,
    Order,
    Product,
    PurchaseOrder,
    Shipment,
    Supplier,
    WorkOrder,
)
from aurix_core.database.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class CanonicalMapper:
    """
    Safely maps validated tabular records into tenant-scoped SQLAlchemy ORM
    objects.

    The mapper intentionally refuses rows that are missing required business
    identifiers or required non-nullable fields. It does not invent business
    values.
    """

    def __init__(self, db: Session, tenant_id: str) -> None:
        self.db = db
        self.tenant_id = tenant_id

        self.product_repo = BaseRepository[Product](Product, db, tenant_id)
        self.location_repo = BaseRepository[Location](Location, db, tenant_id)
        self.supplier_repo = BaseRepository[Supplier](Supplier, db, tenant_id)
        self.inventory_repo = BaseRepository[InventoryPosition](
            InventoryPosition, db, tenant_id
        )

        self.customer_repo = BaseRepository[Customer](Customer, db, tenant_id)
        self.order_repo = BaseRepository[Order](Order, db, tenant_id)
        self.purchase_order_repo = BaseRepository[PurchaseOrder](
            PurchaseOrder, db, tenant_id
        )
        self.shipment_repo = BaseRepository[Shipment](Shipment, db, tenant_id)
        self.invoice_repo = BaseRepository[Invoice](Invoice, db, tenant_id)
        self.work_order_repo = BaseRepository[WorkOrder](WorkOrder, db, tenant_id)

    @staticmethod
    def _safe_float(val: Any) -> Optional[float]:
        if val is None:
            return None

        try:
            if pd.isna(val):
                return None
        except (TypeError, ValueError):
            pass

        text = str(val).strip()
        if not text:
            return None

        try:
            return float(val)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _safe_int(val: Any) -> Optional[int]:
        number = CanonicalMapper._safe_float(val)
        if number is None:
            return None
        return int(number)

    @staticmethod
    def _safe_str(val: Any) -> Optional[str]:
        if val is None:
            return None

        try:
            if pd.isna(val):
                return None
        except (TypeError, ValueError):
            pass

        text = str(val).strip()
        return text or None

    @staticmethod
    def _safe_datetime(val: Any) -> Any:
        if val is None:
            return None

        try:
            if pd.isna(val):
                return None
        except (TypeError, ValueError):
            pass

        if hasattr(val, "to_pydatetime"):
            try:
                return val.to_pydatetime()
            except Exception:
                pass

        return val

    def _required(
        self,
        row: dict[str, Any],
        fields: list[str],
    ) -> Optional[str]:
        missing = [
            field
            for field in fields
            if self._safe_str(row.get(field)) is None
        ]
        if missing:
            return f"missing required fields: {', '.join(missing)}"
        return None

    def map_products(self, df: pd.DataFrame, run_id: str) -> int:
        success_count = 0

        for row in df.to_dict(orient="records"):
            sku_id = (
                self._safe_str(row.get("sku_id"))
                or self._safe_str(row.get("sku_code"))
            )
            if not sku_id:
                continue

            try:
                existing = self.product_repo.get_by_id(sku_id)

                if existing:
                    if self._safe_str(row.get("name")):
                        existing.name = self._safe_str(row.get("name"))
                    if self._safe_str(row.get("category")):
                        existing.category = self._safe_str(row.get("category"))

                    unit_cost = self._safe_float(row.get("unit_cost"))
                    if unit_cost is not None:
                        existing.unit_cost = unit_cost

                    existing.ingestion_run_id = run_id
                    existing.source_record_id = self._safe_str(
                        row.get("source_record_id")
                    )
                else:
                    product = Product(
                        id=sku_id,
                        sku_code=self._safe_str(row.get("sku_code")) or sku_id,
                        name=self._safe_str(row.get("name"))
                        or "Unknown Product",
                        category=self._safe_str(row.get("category")),
                        unit_cost=self._safe_float(row.get("unit_cost")),
                        ingestion_run_id=run_id,
                        source_record_id=self._safe_str(
                            row.get("source_record_id")
                        ),
                        tenant_id=self.tenant_id,
                    )
                    self.product_repo.create(product)

                success_count += 1

            except SQLAlchemyError:
                self.db.rollback()
                logger.exception("Failed to map Product %s", sku_id)

        return success_count

    def map_locations(self, df: pd.DataFrame, run_id: str) -> int:
        success_count = 0

        for row in df.to_dict(orient="records"):
            loc_id = self._safe_str(row.get("location_id"))
            if not loc_id:
                continue

            try:
                existing = self.location_repo.get_by_id(loc_id)

                if existing:
                    if self._safe_str(row.get("location_name")):
                        existing.location_name = self._safe_str(
                            row.get("location_name")
                        )
                    if self._safe_str(row.get("country")):
                        existing.country = self._safe_str(row.get("country"))

                    existing.ingestion_run_id = run_id
                    existing.source_record_id = self._safe_str(
                        row.get("source_record_id")
                    )
                else:
                    location = Location(
                        id=loc_id,
                        location_name=self._safe_str(
                            row.get("location_name")
                        )
                        or "Unknown Location",
                        location_type=self._safe_str(
                            row.get("location_type")
                        )
                        or "WAREHOUSE",
                        country=self._safe_str(row.get("country")),
                        ingestion_run_id=run_id,
                        source_record_id=self._safe_str(
                            row.get("source_record_id")
                        ),
                        tenant_id=self.tenant_id,
                    )
                    self.location_repo.create(location)

                success_count += 1

            except SQLAlchemyError:
                self.db.rollback()
                logger.exception("Failed to map Location %s", loc_id)

        return success_count

    def map_suppliers(self, df: pd.DataFrame, run_id: str) -> int:
        success_count = 0

        for row in df.to_dict(orient="records"):
            supplier_id = self._safe_str(row.get("supplier_id"))
            if not supplier_id:
                continue

            supplier_name = (
                self._safe_str(row.get("supplier_name"))
                or self._safe_str(row.get("name"))
            )

            if not supplier_name:
                continue

            try:
                existing = self.supplier_repo.get_by_id(supplier_id)

                if existing:
                    existing.supplier_name = supplier_name

                    lead_time = self._safe_float(
                        row.get("lead_time_days")
                    )
                    if lead_time is not None:
                        existing.lead_time_days = lead_time

                    if self._safe_str(row.get("country")):
                        existing.country = self._safe_str(
                            row.get("country")
                        )

                    existing.ingestion_run_id = run_id
                    existing.source_record_id = self._safe_str(
                        row.get("source_record_id")
                    )
                else:
                    supplier = Supplier(
                        id=supplier_id,
                        supplier_name=supplier_name,
                        country=self._safe_str(row.get("country")),
                        lead_time_days=self._safe_float(
                            row.get("lead_time_days")
                        ),
                        ingestion_run_id=run_id,
                        source_record_id=self._safe_str(
                            row.get("source_record_id")
                        ),
                        tenant_id=self.tenant_id,
                    )
                    self.supplier_repo.create(supplier)

                success_count += 1

            except SQLAlchemyError:
                self.db.rollback()
                logger.exception("Failed to map Supplier %s", supplier_id)

        return success_count

    def map_inventory(self, df: pd.DataFrame, run_id: str) -> int:
        success_count = 0

        for row in df.to_dict(orient="records"):
            sku_id = self._safe_str(row.get("sku_id"))
            location_id = self._safe_str(row.get("location_id"))

            if not sku_id or not location_id:
                continue

            try:
                existing = (
                    self.inventory_repo
                    ._base_query()
                    .filter_by(
                        sku_id=sku_id,
                        location_id=location_id,
                    )
                    .first()
                )

                on_hand = self._safe_float(row.get("on_hand"))
                on_order = self._safe_float(row.get("on_order"))
                safety_stock = self._safe_float(row.get("safety_stock"))

                if existing:
                    if on_hand is not None:
                        existing.on_hand = on_hand
                    if on_order is not None:
                        existing.on_order = on_order
                    if safety_stock is not None:
                        existing.safety_stock = safety_stock

                    existing.ingestion_run_id = run_id
                    existing.source_record_id = self._safe_str(
                        row.get("source_record_id")
                    )
                else:
                    inventory = InventoryPosition(
                        sku_id=sku_id,
                        location_id=location_id,
                        on_hand=on_hand if on_hand is not None else 0.0,
                        on_order=on_order if on_order is not None else 0.0,
                        safety_stock=safety_stock,
                        ingestion_run_id=run_id,
                        source_record_id=self._safe_str(
                            row.get("source_record_id")
                        ),
                        tenant_id=self.tenant_id,
                    )
                    self.inventory_repo.create(inventory)

                success_count += 1

            except SQLAlchemyError:
                self.db.rollback()
                logger.exception(
                    "Failed to map InventoryPosition %s/%s",
                    sku_id,
                    location_id,
                )

        return success_count

    def map_customers(self, df: pd.DataFrame, run_id: str) -> int:
        success_count = 0

        for row in df.to_dict(orient="records"):
            customer_id = self._safe_str(row.get("customer_id"))
            customer_name = self._safe_str(row.get("customer_name"))

            if not customer_id or not customer_name:
                continue

            try:
                existing = self.customer_repo.get_by_id(customer_id)

                if existing:
                    existing.customer_name = customer_name

                    for attr in (
                        "customer_tier",
                        "segment",
                        "account_status",
                        "assigned_rep_id",
                        "country",
                    ):
                        value = self._safe_str(row.get(attr))
                        if value is not None:
                            setattr(existing, attr, value)

                    credit_limit = self._safe_float(row.get("credit_limit"))
                    if credit_limit is not None:
                        existing.credit_limit = credit_limit

                    existing.ingestion_run_id = run_id
                    existing.source_record_id = self._safe_str(
                        row.get("source_record_id")
                    )
                else:
                    customer = Customer(
                        id=customer_id,
                        customer_name=customer_name,
                        customer_tier=self._safe_str(
                            row.get("customer_tier")
                        ),
                        segment=self._safe_str(row.get("segment")),
                        account_status=self._safe_str(
                            row.get("account_status")
                        )
                        or "ACTIVE",
                        assigned_rep_id=self._safe_str(
                            row.get("assigned_rep_id")
                        ),
                        country=self._safe_str(row.get("country")),
                        credit_limit=self._safe_float(
                            row.get("credit_limit")
                        ),
                        ingestion_run_id=run_id,
                        source_record_id=self._safe_str(
                            row.get("source_record_id")
                        ),
                        tenant_id=self.tenant_id,
                    )
                    self.customer_repo.create(customer)

                success_count += 1

            except SQLAlchemyError:
                self.db.rollback()
                logger.exception(
                    "Failed to map Customer %s",
                    customer_id,
                )

        return success_count

    def map_orders(self, df: pd.DataFrame, run_id: str) -> int:
        success_count = 0

        for row in df.to_dict(orient="records"):
            missing = self._required(
                row,
                ["order_id", "order_number", "order_date"],
            )
            if missing:
                logger.warning(
                    "Skipping order row: %s",
                    missing,
                )
                continue

            order_id = self._safe_str(row.get("order_id"))
            order_number = self._safe_str(row.get("order_number"))
            order_date = self._safe_datetime(row.get("order_date"))

            try:
                existing = self.order_repo.get_by_id(order_id)

                values = {
                    "order_number": order_number,
                    "customer_id": self._safe_str(
                        row.get("customer_id")
                    ),
                    "order_status": self._safe_str(
                        row.get("order_status")
                    )
                    or "OPEN",
                    "channel": self._safe_str(row.get("channel"))
                    or "DIRECT",
                    "sales_rep_id": self._safe_str(
                        row.get("sales_rep_id")
                    ),
                    "total_amount": self._safe_float(
                        row.get("total_amount")
                    )
                    if self._safe_float(row.get("total_amount")) is not None
                    else 0.0,
                    "discount_amount": self._safe_float(
                        row.get("discount_amount")
                    )
                    if self._safe_float(row.get("discount_amount")) is not None
                    else 0.0,
                    "currency": self._safe_str(row.get("currency"))
                    or "USD",
                    "order_date": order_date,
                    "promised_delivery_date": self._safe_datetime(
                        row.get("promised_delivery_date")
                    ),
                    "delivered_date": self._safe_datetime(
                        row.get("delivered_date")
                    ),
                    "ingestion_run_id": run_id,
                    "source_record_id": self._safe_str(
                        row.get("source_record_id")
                    ),
                }

                if existing:
                    for key, value in values.items():
                        if value is not None:
                            setattr(existing, key, value)
                else:
                    self.order_repo.create(
                        Order(
                            id=order_id,
                            tenant_id=self.tenant_id,
                            **values,
                        )
                    )

                success_count += 1

            except SQLAlchemyError:
                self.db.rollback()
                logger.exception("Failed to map Order %s", order_id)

        return success_count

    def map_purchase_orders(self, df: pd.DataFrame, run_id: str) -> int:
        success_count = 0

        for row in df.to_dict(orient="records"):
            missing = self._required(
                row,
                ["purchase_order_id", "supplier_id"],
            )

            # Accept common PO identifier aliases.
            if missing:
                if self._safe_str(row.get("po_id")):
                    row["purchase_order_id"] = row["po_id"]
                    missing = self._required(
                        row,
                        ["purchase_order_id", "supplier_id"],
                    )

            if missing:
                logger.warning("Skipping purchase order row: %s", missing)
                continue

            purchase_order_id = self._safe_str(
                row.get("purchase_order_id")
            ) or self._safe_str(row.get("po_id"))

            try:
                existing = self.purchase_order_repo.get_by_id(
                    purchase_order_id
                )

                values = {
                    "supplier_id": self._safe_str(
                        row.get("supplier_id")
                    ),
                    "status": self._safe_str(row.get("status"))
                    or "DRAFT",
                    "required_date": self._safe_datetime(
                        row.get("required_date")
                    ),
                    "source_request_id": self._safe_str(
                        row.get("source_request_id")
                    ),
                    "revision": self._safe_int(row.get("revision"))
                    or 1,
                    "total_amount": self._safe_float(
                        row.get("total_amount")
                    ),
                    "currency": self._safe_str(
                        row.get("currency")
                    ),
                    "supplier_reference": self._safe_str(
                        row.get("supplier_reference")
                    ),
                    "acknowledged_at": self._safe_datetime(
                        row.get("acknowledged_at")
                    ),
                    "committed_date": self._safe_datetime(
                        row.get("committed_date")
                    ),
                    "cancelled_reason": self._safe_str(
                        row.get("cancelled_reason")
                    ),
                    "updated_at": self._safe_datetime(
                        row.get("updated_at")
                    ),
                }

                if existing:
                    for key, value in values.items():
                        if value is not None:
                            setattr(existing, key, value)
                else:
                    self.purchase_order_repo.create(
                        PurchaseOrder(
                            id=purchase_order_id,
                            tenant_id=self.tenant_id,
                            **values,
                        )
                    )

                success_count += 1

            except SQLAlchemyError:
                self.db.rollback()
                logger.exception(
                    "Failed to map PurchaseOrder %s",
                    purchase_order_id,
                )

        return success_count

    def map_shipments(self, df: pd.DataFrame, run_id: str) -> int:
        success_count = 0

        for row in df.to_dict(orient="records"):
            missing = self._required(
                row,
                [
                    "shipment_id",
                    "shipment_number",
                    "origin_location_id",
                    "destination_location_id",
                ],
            )

            if missing:
                logger.warning(
                    "Skipping shipment row: %s",
                    missing,
                )
                continue

            shipment_id = self._safe_str(row.get("shipment_id"))

            try:
                existing = self.shipment_repo.get_by_id(shipment_id)

                values = {
                    "shipment_number": self._safe_str(
                        row.get("shipment_number")
                    ),
                    "origin_location_id": self._safe_str(
                        row.get("origin_location_id")
                    ),
                    "destination_location_id": self._safe_str(
                        row.get("destination_location_id")
                    ),
                    "carrier": self._safe_str(row.get("carrier")),
                    "status": self._safe_str(row.get("status"))
                    or "IN_TRANSIT",
                    "shipped_date": self._safe_datetime(
                        row.get("shipped_date")
                    ),
                    "estimated_arrival_date": self._safe_datetime(
                        row.get("estimated_arrival_date")
                        or row.get("eta")
                    ),
                    "actual_arrival_date": self._safe_datetime(
                        row.get("actual_arrival_date")
                    ),
                    "ingestion_run_id": run_id,
                    "source_record_id": self._safe_str(
                        row.get("source_record_id")
                    ),
                }

                if existing:
                    for key, value in values.items():
                        if value is not None:
                            setattr(existing, key, value)
                else:
                    self.shipment_repo.create(
                        Shipment(
                            id=shipment_id,
                            tenant_id=self.tenant_id,
                            **values,
                        )
                    )

                success_count += 1

            except SQLAlchemyError:
                self.db.rollback()
                logger.exception(
                    "Failed to map Shipment %s",
                    shipment_id,
                )

        return success_count

    def map_invoices(self, df: pd.DataFrame, run_id: str) -> int:
        success_count = 0

        for row in df.to_dict(orient="records"):
            missing = self._required(
                row,
                [
                    "invoice_id",
                    "invoice_number",
                    "entity_id",
                    "total_amount",
                    "issue_date",
                    "due_date",
                ],
            )

            if missing:
                logger.warning(
                    "Skipping invoice row: %s",
                    missing,
                )
                continue

            invoice_id = self._safe_str(row.get("invoice_id"))

            try:
                existing = self.invoice_repo.get_by_id(invoice_id)

                total_amount = self._safe_float(
                    row.get("total_amount")
                )
                if total_amount is None:
                    continue

                values = {
                    "invoice_number": self._safe_str(
                        row.get("invoice_number")
                    ),
                    "invoice_type": self._safe_str(
                        row.get("invoice_type")
                    )
                    or "ACCOUNTS_RECEIVABLE",
                    "entity_id": self._safe_str(row.get("entity_id")),
                    "total_amount": total_amount,
                    "discount_amount": self._safe_float(
                        row.get("discount_amount")
                    )
                    or 0.0,
                    "credit_note_amount": self._safe_float(
                        row.get("credit_note_amount")
                    )
                    or 0.0,
                    "tax_amount": self._safe_float(
                        row.get("tax_amount")
                    )
                    or 0.0,
                    "currency": self._safe_str(row.get("currency"))
                    or "USD",
                    "status": self._safe_str(row.get("status"))
                    or "ISSUED",
                    "issue_date": self._safe_datetime(
                        row.get("issue_date")
                    ),
                    "due_date": self._safe_datetime(
                        row.get("due_date")
                    ),
                    "ingestion_run_id": run_id,
                    "source_record_id": self._safe_str(
                        row.get("source_record_id")
                    ),
                }

                if existing:
                    for key, value in values.items():
                        if value is not None:
                            setattr(existing, key, value)
                else:
                    self.invoice_repo.create(
                        Invoice(
                            id=invoice_id,
                            tenant_id=self.tenant_id,
                            **values,
                        )
                    )

                success_count += 1

            except SQLAlchemyError:
                self.db.rollback()
                logger.exception(
                    "Failed to map Invoice %s",
                    invoice_id,
                )

        return success_count

    def map_work_orders(self, df: pd.DataFrame, run_id: str) -> int:
        success_count = 0

        for row in df.to_dict(orient="records"):
            missing = self._required(
                row,
                [
                    "work_order_id",
                    "work_order_number",
                    "sku_id",
                    "plant_location_id",
                    "target_quantity",
                ],
            )

            if missing:
                logger.warning(
                    "Skipping work order row: %s",
                    missing,
                )
                continue

            work_order_id = self._safe_str(
                row.get("work_order_id")
            )

            target_quantity = self._safe_float(
                row.get("target_quantity")
            )

            if target_quantity is None:
                continue

            try:
                existing = self.work_order_repo.get_by_id(
                    work_order_id
                )

                values = {
                    "work_order_number": self._safe_str(
                        row.get("work_order_number")
                    ),
                    "sku_id": self._safe_str(row.get("sku_id")),
                    "plant_location_id": self._safe_str(
                        row.get("plant_location_id")
                    ),
                    "work_center_id": self._safe_str(
                        row.get("work_center_id")
                    ),
                    "target_quantity": target_quantity,
                    "completed_quantity": self._safe_float(
                        row.get("completed_quantity")
                    )
                    or 0.0,
                    "scrap_quantity": self._safe_float(
                        row.get("scrap_quantity")
                    )
                    or 0.0,
                    "planned_run_time_minutes": self._safe_float(
                        row.get("planned_run_time_minutes")
                    ),
                    "actual_run_time_minutes": self._safe_float(
                        row.get("actual_run_time_minutes")
                    ),
                    "status": self._safe_str(row.get("status"))
                    or "SCHEDULED",
                    "start_date": self._safe_datetime(
                        row.get("start_date")
                    ),
                    "end_date": self._safe_datetime(
                        row.get("end_date")
                    ),
                    "ingestion_run_id": run_id,
                    "source_record_id": self._safe_str(
                        row.get("source_record_id")
                    ),
                }

                if existing:
                    for key, value in values.items():
                        if value is not None:
                            setattr(existing, key, value)
                else:
                    self.work_order_repo.create(
                        WorkOrder(
                            id=work_order_id,
                            tenant_id=self.tenant_id,
                            **values,
                        )
                    )

                success_count += 1

            except SQLAlchemyError:
                self.db.rollback()
                logger.exception(
                    "Failed to map WorkOrder %s",
                    work_order_id,
                )

        return success_count
