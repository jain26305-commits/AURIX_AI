"""
AURIX Deterministic Evidence Fabric.

Provides tenant-scoped, read-only retrieval of authoritative evidence
from canonical and intelligence persistence layers.

This layer deliberately does NOT invent metrics. Missing source data is
represented explicitly as unavailable evidence.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from aurix_core.database.models.supply_chain import (
    Product,
    InventoryPosition,
    Order,
    OrderLine,
    Supplier,
)
from aurix_core.database.models.supply_intelligence import (
    SupplierPerformance as CanonicalSupplierPerformance,
)

from aurix_core.database.models.inventory_intelligence import ReplenishmentPolicy
from aurix_core.database.models.forecasting import ForecastPoint, ForecastRun
from aurix_core.database.models.logistics_intelligence import ShipmentEvaluation
from aurix_core.database.models.supply_chain import Shipment, InventoryTransaction


class EvidenceItem(BaseModel):
    source: str
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    available: bool = False
    records: List[Dict[str, Any]] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    provenance: Dict[str, Any] = Field(default_factory=dict)


class EvidencePack(BaseModel):
    tenant_id: str
    query: str
    items: List[EvidenceItem] = Field(default_factory=list)

    @property
    def available_sources(self) -> List[str]:
        return [
            item.source
            for item in self.items
            if item.available
        ]

    @property
    def unavailable_sources(self) -> List[str]:
        return [
            item.source
            for item in self.items
            if not item.available
        ]

    def all_records(self) -> List[Dict[str, Any]]:
        output: List[Dict[str, Any]] = []

        for item in self.items:
            for record in item.records:
                output.append(
                    {
                        "_evidence_source": item.source,
                        "_evidence_entity_type": item.entity_type,
                        "_evidence_entity_id": item.entity_id,
                        **record,
                    }
                )

        return output


class EvidenceFabric:
    """
    Read-only evidence retrieval boundary for deterministic AURIX answers.
    """

    @staticmethod
    def _serialize(obj: Any, fields: List[str]) -> Dict[str, Any]:
        result: Dict[str, Any] = {}

        for field in fields:
            if not hasattr(obj, field):
                raise AttributeError(
                    f"Evidence schema mismatch: "
                    f"{type(obj).__name__} has no field '{field}'."
                )

            value = getattr(obj, field)

            if isinstance(value, datetime):
                value = value.isoformat()

            result[field] = value

        return result

    @classmethod
    def product(
        cls,
        db: Session,
        tenant_id: str,
        entity_id: Optional[str] = None,
    ) -> EvidenceItem:

        stmt = (
            select(Product)
            .where(Product.tenant_id == tenant_id)
            .order_by(desc(Product.created_at))
            .limit(50)
        )

        if entity_id:
            stmt = stmt.where(
                (Product.id == entity_id)
                | (Product.sku_code == entity_id)
            )

        rows = list(db.execute(stmt).scalars())

        return EvidenceItem(
            source="product",
            entity_type="product",
            entity_id=entity_id,
            available=bool(rows),
            records=[
                cls._serialize(
                    row,
                    [
                        "id",
                        "sku_code",
                        "name",
                        "category",
                        "unit_cost",
                        "created_at",
                    ],
                )
                for row in rows
            ],
            limitations=[]
            if rows
            else ["NO_PRODUCT_DATA"],
            provenance={
                "source_table": "products",
                "tenant_id": tenant_id,
            },
        )

    @classmethod
    def inventory_position(
        cls,
        db: Session,
        tenant_id: str,
        entity_id: Optional[str] = None,
        location_id: Optional[str] = None,
    ) -> EvidenceItem:

        stmt = (
            select(InventoryPosition)
            .where(
                InventoryPosition.tenant_id == tenant_id
            )
            .order_by(desc(InventoryPosition.updated_at))
            .limit(100)
        )

        if entity_id:
            stmt = stmt.where(
                InventoryPosition.sku_id == entity_id
            )

        if location_id:
            stmt = stmt.where(
                InventoryPosition.location_id == location_id
            )

        rows = list(db.execute(stmt).scalars())

        return EvidenceItem(
            source="inventory_position",
            entity_type="inventory",
            entity_id=entity_id,
            available=bool(rows),
            records=[
                cls._serialize(
                    row,
                    [
                        "id",
                        "sku_id",
                        "location_id",
                        "on_hand",
                        "on_order",
                        "safety_stock",
                        "updated_at",
                        "source_record_id",
                        "ingestion_run_id",
                    ],
                )
                for row in rows
            ],
            limitations=[]
            if rows
            else ["NO_CANONICAL_INVENTORY_DATA"],
            provenance={
                "source_table": "inventory_positions",
                "tenant_id": tenant_id,
                "entity_id": entity_id,
                "location_id": location_id,
            },
        )

    @classmethod
    def orders(
        cls,
        db: Session,
        tenant_id: str,
        entity_id: Optional[str] = None,
    ) -> EvidenceItem:

        stmt = (
            select(Order)
            .where(Order.tenant_id == tenant_id)
            .order_by(desc(Order.order_date))
            .limit(100)
        )

        rows = list(db.execute(stmt).scalars())

        return EvidenceItem(
            source="orders",
            entity_type="order",
            entity_id=entity_id,
            available=bool(rows),
            records=[
                cls._serialize(
                    row,
                    [
                        "id",
                        "order_number",
                        "customer_id",
                        "order_status",
                        "channel",
                        "total_amount",
                        "discount_amount",
                        "currency",
                        "order_date",
                        "promised_delivery_date",
                        "delivered_date",
                    ],
                )
                for row in rows
            ],
            limitations=[]
            if rows
            else ["NO_ORDER_DATA"],
            provenance={
                "source_table": "orders",
                "tenant_id": tenant_id,
            },
        )

    @classmethod
    def order_lines(
        cls,
        db: Session,
        tenant_id: str,
        entity_id: Optional[str] = None,
    ) -> EvidenceItem:

        stmt = (
            select(OrderLine)
            .where(OrderLine.tenant_id == tenant_id)
            .limit(250)
        )

        if entity_id:
            stmt = stmt.where(OrderLine.sku_id == entity_id)

        rows = list(db.execute(stmt).scalars())

        return EvidenceItem(
            source="order_lines",
            entity_type="order_line",
            entity_id=entity_id,
            available=bool(rows),
            records=[
                cls._serialize(
                    row,
                    [
                        "id",
                        "order_id",
                        "sku_id",
                        "quantity",
                        "unit_price",
                        "discount_amount",
                        "sales_channel",
                        "line_total",
                    ],
                )
                for row in rows
            ],
            limitations=[]
            if rows
            else ["NO_ORDER_LINE_DATA"],
            provenance={
                "source_table": "order_lines",
                "tenant_id": tenant_id,
            },
        )

    @classmethod
    def suppliers(
        cls,
        db: Session,
        tenant_id: str,
        entity_id: Optional[str] = None,
    ) -> EvidenceItem:

        stmt = (
            select(Supplier)
            .where(Supplier.tenant_id == tenant_id)
            .order_by(desc(Supplier.created_at))
            .limit(100)
        )

        if entity_id:
            stmt = stmt.where(Supplier.id == entity_id)

        rows = list(db.execute(stmt).scalars())

        return EvidenceItem(
            source="suppliers",
            entity_type="supplier",
            entity_id=entity_id,
            available=bool(rows),
            records=[
                cls._serialize(
                    row,
                    [
                        "id",
                        "supplier_name",
                        "country",
                        "lead_time_days",
                        "created_at",
                    ],
                )
                for row in rows
            ],
            limitations=[]
            if rows
            else ["NO_SUPPLIER_DATA"],
            provenance={
                "source_table": "suppliers",
                "tenant_id": tenant_id,
            },
        )

    @classmethod
    def supplier_performance(
        cls,
        db: Session,
        tenant_id: str,
        entity_id: Optional[str] = None,
    ) -> EvidenceItem:

        stmt = (
            select(CanonicalSupplierPerformance)
            .where(
                CanonicalSupplierPerformance.tenant_id == tenant_id
            )
            .order_by(
                desc(
                    CanonicalSupplierPerformance.evaluated_at
                )
            )
            .limit(100)
        )

        if entity_id:
            stmt = stmt.where(
                CanonicalSupplierPerformance.supplier_id
                == entity_id
            )

        rows = list(db.execute(stmt).scalars())

        return EvidenceItem(
            source="supplier_performance",
            entity_type="supplier",
            entity_id=entity_id,
            available=bool(rows),
            records=[
                cls._serialize(
                    row,
                    [
                        "supplier_id",
                        "evaluated_order_count",
                        "otd_rate",
                        "in_full_rate",
                        "otif_rate",
                        "mean_lead_time_days",
                        "lead_time_std_days",
                        "risk_score",
                        "risk_level",
                        "risk_drivers",
                        "value_state",
                        "created_at",
                    ],
                )
                for row in rows
            ],
            limitations=[]
            if rows
            else ["NO_SUPPLIER_PERFORMANCE_DATA"],
            provenance={
                "source_table": "supplier_performance",
                "tenant_id": tenant_id,
            },
        )

    @classmethod
    def shipments(
        cls,
        db: Session,
        tenant_id: str,
        entity_id: Optional[str] = None,
    ) -> EvidenceItem:

        stmt = (
            select(Shipment)
            .where(Shipment.tenant_id == tenant_id)
            .order_by(desc(Shipment.created_at))
            .limit(100)
        )

        if entity_id:
            stmt = stmt.where(
                (Shipment.id == entity_id)
                | (Shipment.shipment_number == entity_id)
            )

        rows = list(db.execute(stmt).scalars())

        return EvidenceItem(
            source="shipments",
            entity_type="shipment",
            entity_id=entity_id,
            available=bool(rows),
            records=[
                cls._serialize(
                    row,
                    [
                        "id",
                        "shipment_number",
                        "origin_location_id",
                        "destination_location_id",
                        "carrier",
                        "status",
                        "shipped_date",
                        "estimated_arrival_date",
                        "actual_arrival_date",
                    ],
                )
                for row in rows
            ],
            limitations=[]
            if rows
            else ["NO_SHIPMENT_DATA"],
            provenance={
                "source_table": "shipments",
                "tenant_id": tenant_id,
            },
        )

    @classmethod
    def replenishment_policy(
        cls,
        db: Session,
        tenant_id: str,
        entity_id: Optional[str] = None,
    ) -> EvidenceItem:

        stmt = (
            select(ReplenishmentPolicy)
            .where(
                ReplenishmentPolicy.tenant_id == tenant_id
            )
            .order_by(
                desc(ReplenishmentPolicy.created_at)
            )
            .limit(100)
        )

        if entity_id:
            stmt = stmt.where(
                ReplenishmentPolicy.sku_id == entity_id
            )

        rows = list(db.execute(stmt).scalars())

        return EvidenceItem(
            source="replenishment_policy",
            entity_type="inventory",
            entity_id=entity_id,
            available=bool(rows),
            records=[
                cls._serialize(
                    row,
                    [
                        "id",
                        "run_id",
                        "sku_id",
                        "location_id",
                        "expected_daily_demand",
                        "lead_time_days",
                        "safety_stock",
                        "reorder_point",
                        "eoq",
                        "reorder_triggered",
                        "reorder_reason",
                        "raw_order_quantity",
                        "constrained_order_quantity",
                        "risk_status",
                        "holding_cost_exposure",
                        "value_state",
                        "created_at",
                    ],
                )
                for row in rows
            ],
            limitations=[]
            if rows
            else ["NO_REPLENISHMENT_POLICY_DATA"],
            provenance={
                "source_table": "replenishment_policies",
                "tenant_id": tenant_id,
            },
        )

    @classmethod
    def forecast(
        cls,
        db: Session,
        tenant_id: str,
        entity_id: Optional[str] = None,
    ) -> EvidenceItem:

        latest_run = db.execute(
            select(ForecastRun)
            .where(
                ForecastRun.tenant_id == tenant_id,
                ForecastRun.status == "COMPLETED",
            )
            .order_by(desc(ForecastRun.created_at))
            .limit(1)
        ).scalar_one_or_none()

        if latest_run is None:
            return EvidenceItem(
                source="forecast",
                entity_type="forecast",
                entity_id=entity_id,
                limitations=["NO_COMPLETED_FORECAST_RUN"],
                provenance={
                    "source_tables": [
                        "forecast_runs",
                        "forecast_points",
                    ],
                    "tenant_id": tenant_id,
                },
            )

        stmt = (
            select(ForecastPoint)
            .where(
                ForecastPoint.tenant_id == tenant_id,
                ForecastPoint.forecast_run_id == latest_run.id,
            )
            .order_by(ForecastPoint.target_date)
            .limit(250)
        )

        if entity_id:
            stmt = stmt.where(
                ForecastPoint.sku_id == entity_id
            )

        rows = list(db.execute(stmt).scalars())

        return EvidenceItem(
            source="forecast",
            entity_type="forecast",
            entity_id=entity_id,
            available=bool(rows),
            records=[
                cls._serialize(
                    row,
                    [
                        "forecast_run_id",
                        "sku_id",
                        "location_id",
                        "target_date",
                        "horizon_step",
                        "point_forecast",
                        "raw_model_forecast",
                        "lower_bound",
                        "upper_bound",
                        "model_id",
                        "value_state",
                    ],
                )
                for row in rows
            ],
            limitations=[]
            if rows
            else ["NO_FORECAST_POINTS"],
            provenance={
                "source_tables": [
                    "forecast_runs",
                    "forecast_points",
                ],
                "forecast_run_id": latest_run.id,
                "tenant_id": tenant_id,
            },
        )

    @classmethod
    def inventory_transactions(
        cls,
        db: Session,
        tenant_id: str,
        entity_id: Optional[str] = None,
    ) -> EvidenceItem:

        stmt = (
            select(InventoryTransaction)
            .where(
                InventoryTransaction.tenant_id == tenant_id
            )
            .order_by(
                desc(InventoryTransaction.transaction_date)
            )
            .limit(250)
        )

        if entity_id:
            stmt = stmt.where(
                InventoryTransaction.sku_id == entity_id
            )

        rows = list(db.execute(stmt).scalars())

        return EvidenceItem(
            source="inventory_transactions",
            entity_type="inventory_transaction",
            entity_id=entity_id,
            available=bool(rows),
            records=[
                cls._serialize(
                    row,
                    [
                        "id",
                        "sku_id",
                        "location_id",
                        "transaction_type",
                        "quantity",
                        "reference_document",
                        "transaction_date",
                    ],
                )
                for row in rows
            ],
            limitations=[]
            if rows
            else ["NO_INVENTORY_TRANSACTION_DATA"],
            provenance={
                "source_table": "inventory_transactions",
                "tenant_id": tenant_id,
            },
        )

    @classmethod
    def collect(
        cls,
        db: Session,
        tenant_id: str,
        query: str,
        sources: List[str],
        entity_id: Optional[str] = None,
        location_id: Optional[str] = None,
    ) -> EvidencePack:

        handlers = {
            "product": cls.product,
            "inventory_position": cls.inventory_position,
            "orders": cls.orders,
            "order_lines": cls.order_lines,
            "suppliers": cls.suppliers,
            "supplier_performance": cls.supplier_performance,
            "shipments": cls.shipments,
            "replenishment_policy": cls.replenishment_policy,
            "forecast": cls.forecast,
            "inventory_transactions": cls.inventory_transactions,
        }

        items: List[EvidenceItem] = []

        for source in sources:
            handler = handlers.get(source)

            if handler is None:
                items.append(
                    EvidenceItem(
                        source=source,
                        entity_id=entity_id,
                        limitations=[
                            "UNREGISTERED_EVIDENCE_SOURCE"
                        ],
                    )
                )
                continue

            if source == "inventory_position":
                items.append(
                    handler(
                        db=db,
                        tenant_id=tenant_id,
                        entity_id=entity_id,
                        location_id=location_id,
                    )
                )
            else:
                items.append(
                    handler(
                        db=db,
                        tenant_id=tenant_id,
                        entity_id=entity_id,
                    )
                )

        return EvidencePack(
            tenant_id=tenant_id,
            query=query,
            items=items,
        )
