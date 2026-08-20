"""Central registry for deterministic AURIX tools.

The registry deliberately wraps existing Phase 1-15 persistence/calculation
outputs instead of reimplementing domain mathematics.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from aurix_core.database.models.economics import FinancialBaselineSnapshot
from aurix_core.database.models.forecasting import ForecastPoint, ForecastRun
from aurix_core.database.models.intelligence import IntelligenceSnapshotModel
from aurix_core.database.models.supply_chain import InventoryPosition
from aurix_core.database.repositories.inventory_intelligence import (
    ReplenishmentPolicyRepository,
)
from aurix_core.database.repositories.logistics_intelligence import (
    ShipmentEvaluationRepository,
)
from aurix_core.database.repositories.supply_intelligence import (
    SupplierPerformanceRepository,
)
from aurix_core.intelligence.discovery import Domain
from aurix_core.phase16.contracts import (
    ATPRequest,
    CTPRequest,
    CapacityCheckRequest,
    MRPRequest,
    ScenarioComparisonRequest,
    ScenarioRequest,
)
from aurix_core.phase16.services import (
    CapacityService,
    FulfillmentService,
    ManufacturingService,
    ScenarioService,
)
from aurix_core.tools.contracts import (
    ToolDefinition,
    ToolRequest,
    ToolResult,
)

logger = logging.getLogger(__name__)

CAPABILITY_TO_TOOL: Dict[str, str] = {
    "DEMAND_FORECASTING": "forecast.latest",
    "SAFETY_STOCK_ROP": "inventory.replenishment_policy",
    "INVENTORY_POSITION_RISK": "inventory.position",
    "SUPPLIER_PERFORMANCE_RISK": "supplier.performance",
    "SHIPMENT_TRACKING_ETA": "logistics.shipment",
    "NETWORK_TOPOLOGY_BOTTLENECK": "intelligence.snapshot",
    "INVENTORY_REBALANCING": "intelligence.snapshot",
    "PORTFOLIO_SNAPSHOT": "intelligence.snapshot",
    "WORKING_CAPITAL_TCO": "economics.baseline",
    "PHASE16_ATP": "phase16.atp",
    "PHASE16_CTP": "phase16.ctp",
    "PHASE16_MRP": "phase16.mrp",
    "PHASE16_CAPACITY": "phase16.capacity",
    "PHASE16_SCENARIO": "phase16.scenario",
    "PHASE16_SCENARIO_COMPARE": "phase16.scenario_compare",
}


def _serialize_model(obj: Any, fields: list[str]) -> Dict[str, Any]:
    """Serialize only explicitly approved fields from an ORM object."""
    return {field: getattr(obj, field, None) for field in fields}


def _missing_entity(tool_name: str, capability: Optional[str] = None) -> ToolResult:
    return ToolResult(
        success=False,
        tool_name=tool_name,
        capability=capability,
        answer="A specific entity is required for this deterministic query.",
        limitations=["ENTITY_REQUIRED"],
    )


def _inventory_position(db: Session, req: ToolRequest) -> ToolResult:
    if not req.entity_id:
        return _missing_entity("inventory.position", "INVENTORY_POSITION_RISK")

    rows = list(
        db.execute(
            select(InventoryPosition)
            .where(
                InventoryPosition.tenant_id == req.tenant_id,
                InventoryPosition.sku_id == req.entity_id,
            )
            .order_by(desc(InventoryPosition.updated_at))
            .limit(100)
        ).scalars()
    )

    if not rows:
        return ToolResult(
            success=False,
            tool_name="inventory.position",
            capability="INVENTORY_POSITION_RISK",
            answer=f"No inventory position is available for {req.entity_id}.",
            limitations=["NO_CANONICAL_INVENTORY_DATA"],
        )

    positions = [
        _serialize_model(
            row,
            ["sku_id", "location_id", "on_hand", "on_order", "safety_stock", "updated_at"],
        )
        for row in rows
    ]
    return ToolResult(
        success=True,
        tool_name="inventory.position",
        capability="INVENTORY_POSITION_RISK",
        answer=f"AURIX found {len(positions)} inventory position(s) for {req.entity_id}.",
        data={"positions": positions},
        provenance={
            "source_tables": ["inventory_positions"],
            "tenant_id": req.tenant_id,
            "entity_id": req.entity_id,
        },
    )


def _inventory_policy(db: Session, req: ToolRequest) -> ToolResult:
    if not req.entity_id:
        return _missing_entity("inventory.replenishment_policy", "SAFETY_STOCK_ROP")

    policy = ReplenishmentPolicyRepository(
        db, req.tenant_id
    ).get_latest_by_sku(req.entity_id)
    if policy is None:
        return ToolResult(
            success=False,
            tool_name="inventory.replenishment_policy",
            capability="SAFETY_STOCK_ROP",
            answer=f"No replenishment policy is available for {req.entity_id}.",
            limitations=["NO_REPLENISHMENT_POLICY"],
        )

    data = _serialize_model(
        policy,
        [
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
    return ToolResult(
        success=True,
        tool_name="inventory.replenishment_policy",
        capability="SAFETY_STOCK_ROP",
        answer=f"AURIX found the latest replenishment policy for {req.entity_id}.",
        data=data,
        provenance={
            "source_tables": ["replenishment_policies"],
            "tenant_id": req.tenant_id,
            "entity_id": req.entity_id,
        },
    )


def _latest_forecast(db: Session, req: ToolRequest) -> ToolResult:
    if not req.entity_id:
        return _missing_entity("forecast.latest", "DEMAND_FORECASTING")

    latest_run = db.execute(
        select(ForecastRun)
        .where(
            ForecastRun.tenant_id == req.tenant_id,
            ForecastRun.status == "COMPLETED",
        )
        .order_by(desc(ForecastRun.created_at))
        .limit(1)
    ).scalar_one_or_none()

    if latest_run is None:
        return ToolResult(
            success=False,
            tool_name="forecast.latest",
            capability="DEMAND_FORECASTING",
            answer="No completed forecast run is available.",
            limitations=["NO_COMPLETED_FORECAST_RUN"],
        )

    points = list(
        db.execute(
            select(ForecastPoint)
            .where(
                ForecastPoint.tenant_id == req.tenant_id,
                ForecastPoint.forecast_run_id == latest_run.id,
                ForecastPoint.sku_id == req.entity_id,
            )
            .order_by(ForecastPoint.target_date)
            .limit(100)
        ).scalars()
    )

    if not points:
        return ToolResult(
            success=False,
            tool_name="forecast.latest",
            capability="DEMAND_FORECASTING",
            answer=f"No forecast points are available for {req.entity_id} in the latest completed run.",
            limitations=["NO_FORECAST_POINTS_FOR_ENTITY"],
        )

    data = {
        "forecast_run_id": latest_run.id,
        "horizon": latest_run.horizon,
        "frequency": latest_run.frequency,
        "points": [
            _serialize_model(
                point,
                [
                    "sku_id",
                    "location_id",
                    "target_date",
                    "horizon_step",
                    "point_forecast",
                    "lower_bound",
                    "upper_bound",
                    "model_id",
                    "value_state",
                ],
            )
            for point in points
        ],
    }
    return ToolResult(
        success=True,
        tool_name="forecast.latest",
        capability="DEMAND_FORECASTING",
        answer=f"AURIX found {len(points)} forecast point(s) for {req.entity_id}.",
        data=data,
        provenance={
            "source_tables": ["forecast_runs", "forecast_points"],
            "forecast_run_id": latest_run.id,
            "tenant_id": req.tenant_id,
            "entity_id": req.entity_id,
        },
    )


def _supplier_performance(db: Session, req: ToolRequest) -> ToolResult:
    if not req.entity_id:
        return _missing_entity("supplier.performance", "SUPPLIER_PERFORMANCE_RISK")

    record = SupplierPerformanceRepository(
        db, req.tenant_id
    ).get_latest_by_supplier(req.entity_id)
    if record is None:
        return ToolResult(
            success=False,
            tool_name="supplier.performance",
            capability="SUPPLIER_PERFORMANCE_RISK",
            answer=f"No supplier performance record is available for {req.entity_id}.",
            limitations=["NO_SUPPLIER_PERFORMANCE"],
        )

    data = _serialize_model(
        record,
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
    return ToolResult(
        success=True,
        tool_name="supplier.performance",
        capability="SUPPLIER_PERFORMANCE_RISK",
        answer=f"AURIX found the latest supplier performance record for {req.entity_id}.",
        data=data,
        provenance={
            "source_tables": ["supplier_performance"],
            "supplier_id": req.entity_id,
            "tenant_id": req.tenant_id,
        },
    )


def _logistics_shipment(db: Session, req: ToolRequest) -> ToolResult:
    if not req.entity_id:
        return _missing_entity("logistics.shipment", "SHIPMENT_TRACKING_ETA")

    record = ShipmentEvaluationRepository(
        db, req.tenant_id
    ).get_by_shipment_id(req.entity_id)
    if record is None:
        return ToolResult(
            success=False,
            tool_name="logistics.shipment",
            capability="SHIPMENT_TRACKING_ETA",
            answer=f"No shipment evaluation is available for {req.entity_id}.",
            limitations=["NO_SHIPMENT_EVALUATION"],
        )

    data = _serialize_model(
        record,
        [
            "shipment_id",
            "order_id",
            "sku_id",
            "carrier_id",
            "origin_id",
            "destination_id",
            "quantity",
            "dispatch_date",
            "promised_delivery_date",
            "estimated_delivery_date",
            "actual_delivery_date",
            "eta_source",
            "delay_hours",
            "is_delayed",
            "logistics_risk_score",
            "risk_level",
            "expedite_recommendation",
            "recommendation_reason",
            "freight_cost",
            "currency",
            "value_state",
        ],
    )
    return ToolResult(
        success=True,
        tool_name="logistics.shipment",
        capability="SHIPMENT_TRACKING_ETA",
        answer=f"AURIX found the latest shipment evaluation for {req.entity_id}.",
        data=data,
        provenance={
            "source_tables": ["shipment_evaluations"],
            "shipment_id": req.entity_id,
            "tenant_id": req.tenant_id,
        },
    )


def _financial_baseline(db: Session, req: ToolRequest) -> ToolResult:
    record = db.execute(
        select(FinancialBaselineSnapshot)
        .where(FinancialBaselineSnapshot.tenant_id == req.tenant_id)
        .order_by(desc(FinancialBaselineSnapshot.run_id))
        .limit(1)
    ).scalar_one_or_none()
    if record is None:
        return ToolResult(
            success=False,
            tool_name="economics.baseline",
            capability="WORKING_CAPITAL_TCO",
            answer="No persisted financial baseline is available.",
            limitations=["NO_FINANCIAL_BASELINE"],
        )
    try:
        metrics = json.loads(str(record.baseline_metrics_json or "{}"))
    except (TypeError, ValueError):
        metrics = {}
    return ToolResult(
        success=True,
        tool_name="economics.baseline",
        capability="WORKING_CAPITAL_TCO",
        answer="AURIX found the latest persisted financial baseline.",
        data={"run_id": record.run_id, "currency": record.currency, "metrics": metrics},
        provenance={
            "source_tables": ["financial_baseline_snapshots"],
            "run_id": record.run_id,
            "tenant_id": req.tenant_id,
        },
    )


def _intelligence_snapshot(db: Session, req: ToolRequest) -> ToolResult:
    record = db.execute(
        select(IntelligenceSnapshotModel)
        .where(IntelligenceSnapshotModel.tenant_id == req.tenant_id)
        .order_by(desc(IntelligenceSnapshotModel.created_at))
        .limit(1)
    ).scalar_one_or_none()

    if record is None:
        return ToolResult(
            success=False,
            tool_name="intelligence.snapshot",
            capability="PORTFOLIO_SNAPSHOT",
            answer="No persisted intelligence snapshot is available.",
            limitations=["NO_INTELLIGENCE_SNAPSHOT"],
        )

    try:
        payload = json.loads(str(record.snapshot_json))
    except (TypeError, ValueError):
        payload = {}

    return ToolResult(
        success=True,
        tool_name="intelligence.snapshot",
        capability="PORTFOLIO_SNAPSHOT",
        answer="AURIX found the latest persisted intelligence snapshot.",
        data={"snapshot_id": record.id, "run_id": record.run_id, "snapshot": payload},
        provenance={
            "source_tables": ["intelligence_snapshots"],
            "snapshot_id": record.id,
            "run_id": record.run_id,
            "tenant_id": req.tenant_id,
        },
    )


def _phase16_atp(db: Session, req: ToolRequest) -> ToolResult:
    if not req.entity_id:
        return _missing_entity("phase16.atp", "PHASE16_ATP")

    params = req.parameters or {}
    try:
        requested = float(params.get("requested_quantity", 0))
    except (TypeError, ValueError):
        requested = 0.0

    if requested <= 0:
        return ToolResult(
            success=False,
            tool_name="phase16.atp",
            capability="PHASE16_ATP",
            answer="A positive requested_quantity is required.",
            limitations=["INVALID_REQUESTED_QUANTITY"],
        )
    result = FulfillmentService.calculate_atp(
        db,
        req.tenant_id,
        ATPRequest(
            sku_id=req.entity_id,
            requested_quantity=requested,
            location_id=params.get("location_id"),
        ),
    )
    return ToolResult(
        success=result.success,
        tool_name="phase16.atp",
        capability="PHASE16_ATP",
        answer=f"ATP evaluation for {req.entity_id}: {result.status}.",
        data=result.data,
        provenance={"phase16_status": result.status, "tenant_id": req.tenant_id},
        limitations=result.warnings,
    )


def _phase16_ctp(db: Session, req: ToolRequest) -> ToolResult:
    if not req.entity_id:
        return _missing_entity("phase16.ctp", "PHASE16_CTP")

    params = req.parameters or {}
    raw = {
        "sku_id": req.entity_id,
        "requested_quantity": params.get("requested_quantity"),
        "location_id": params.get("location_id"),
        "requested_date": params.get("requested_date"),
        "production_lead_time_days": params.get("production_lead_time_days"),
        "capacity_resources": params.get("capacity_resources", []),
    }
    try:
        request = CTPRequest.model_validate(raw)
    except Exception as exc:
        return ToolResult(
            success=False,
            tool_name="phase16.ctp",
            capability="PHASE16_CTP",
            answer="CTP request failed validation.",
            limitations=[f"INVALID_CTP_REQUEST:{exc}"],
        )
    result = FulfillmentService.calculate_ctp(db, req.tenant_id, request)
    return ToolResult(
        success=result.success,
        tool_name="phase16.ctp",
        capability="PHASE16_CTP",
        answer=f"CTP evaluation for {req.entity_id}: {result.status}.",
        data=result.data,
        provenance={"phase16_status": result.status, "tenant_id": req.tenant_id},
        limitations=result.warnings,
    )


def _phase16_mrp(db: Session, req: ToolRequest) -> ToolResult:
    params = req.parameters or {}
    raw_requirements = params.get("requirements")
    if not isinstance(raw_requirements, list) or not raw_requirements:
        return ToolResult(
            success=False,
            tool_name="phase16.mrp",
            capability="PHASE16_MRP",
            answer="MRP requires a non-empty requirements list.",
            limitations=["MRP_REQUIREMENTS_REQUIRED"],
        )
    try:
        request = MRPRequest.model_validate({"requirements": raw_requirements})
    except Exception as exc:
        return ToolResult(
            success=False,
            tool_name="phase16.mrp",
            capability="PHASE16_MRP",
            answer="MRP requirements failed validation.",
            limitations=[f"INVALID_MRP_REQUEST:{exc}"],
        )
    result = ManufacturingService.run_mrp(db, req.tenant_id, request)
    return ToolResult(
        success=result.success,
        tool_name="phase16.mrp",
        capability="PHASE16_MRP",
        answer="MRP completed deterministically." if result.success else "MRP could not be completed.",
        data=result.data,
        provenance={"phase16_status": result.status, "tenant_id": req.tenant_id},
        limitations=result.warnings,
    )


def _phase16_capacity(db: Session, req: ToolRequest) -> ToolResult:
    params = req.parameters or {}
    raw_resources = params.get("resources")
    if not isinstance(raw_resources, list) or not raw_resources:
        return ToolResult(
            success=False,
            tool_name="phase16.capacity",
            capability="PHASE16_CAPACITY",
            answer="Capacity checking requires a non-empty resources list.",
            limitations=["CAPACITY_RESOURCES_REQUIRED"],
        )
    try:
        request = CapacityCheckRequest.model_validate({"resources": raw_resources})
    except Exception as exc:
        return ToolResult(
            success=False,
            tool_name="phase16.capacity",
            capability="PHASE16_CAPACITY",
            answer="Capacity request failed validation.",
            limitations=[f"INVALID_CAPACITY_REQUEST:{exc}"],
        )
    result = CapacityService.check(db, req.tenant_id, request)
    return ToolResult(
        success=result.success,
        tool_name="phase16.capacity",
        capability="PHASE16_CAPACITY",
        answer=f"Capacity status: {result.status}.",
        data=result.data,
        provenance={"phase16_status": result.status, "tenant_id": req.tenant_id},
        limitations=result.warnings,
    )


def _phase16_scenario(db: Session, req: ToolRequest) -> ToolResult:
    params = req.parameters or {}
    scenario_type = str(params.get("scenario_type", "")).strip()
    parameters = params.get("parameters", {})
    if not scenario_type or not isinstance(parameters, dict):
        return ToolResult(
            success=False,
            tool_name="phase16.scenario",
            capability="PHASE16_SCENARIO",
            answer="scenario_type and parameters are required.",
            limitations=["INVALID_SCENARIO_REQUEST"],
        )
    result = ScenarioService.run(
        db,
        req.tenant_id,
        ScenarioRequest(scenario_type=scenario_type, parameters=parameters),
    )
    return ToolResult(
        success=result.success,
        tool_name="phase16.scenario",
        capability="PHASE16_SCENARIO",
        answer=f"Scenario status: {result.status}.",
        data=result.data,
        provenance={"phase16_status": result.status, "tenant_id": req.tenant_id},
        limitations=result.warnings,
    )


def _phase16_scenario_compare(db: Session, req: ToolRequest) -> ToolResult:
    params = req.parameters or {}
    raw_scenarios = params.get("scenarios")
    if not isinstance(raw_scenarios, list) or len(raw_scenarios) < 2:
        return ToolResult(
            success=False,
            tool_name="phase16.scenario_compare",
            capability="PHASE16_SCENARIO_COMPARE",
            answer="Scenario comparison requires at least two scenarios.",
            limitations=["SCENARIOS_REQUIRED"],
        )
    try:
        request = ScenarioComparisonRequest.model_validate({"scenarios": raw_scenarios})
    except Exception as exc:
        return ToolResult(
            success=False,
            tool_name="phase16.scenario_compare",
            capability="PHASE16_SCENARIO_COMPARE",
            answer="Scenario comparison failed validation.",
            limitations=[f"INVALID_SCENARIO_COMPARISON:{exc}"],
        )
    result = ScenarioService.compare(db, req.tenant_id, request)
    return ToolResult(
        success=result.success,
        tool_name="phase16.scenario_compare",
        capability="PHASE16_SCENARIO_COMPARE",
        answer="Scenario comparison completed." if result.success else "Scenario comparison failed.",
        data=result.data,
        provenance={"phase16_status": result.status, "tenant_id": req.tenant_id},
        limitations=result.warnings,
    )


class ToolRegistry:
    """Tenant-safe registry of deterministic, read-only AURIX capabilities."""

    _definitions: Dict[str, ToolDefinition] = {}

    @classmethod
    def register(cls, definition: ToolDefinition) -> None:
        cls._definitions[definition.name] = definition

    @classmethod
    def get(cls, name: str) -> Optional[ToolDefinition]:
        return cls._definitions.get(name)

    @classmethod
    def resolve_for_capability(cls, capability: Optional[str]) -> Optional[ToolDefinition]:
        if not capability:
            return None
        tool_name = CAPABILITY_TO_TOOL.get(capability)
        return cls.get(tool_name) if tool_name else None

    @classmethod
    def list_definitions(cls) -> List[ToolDefinition]:
        return list(cls._definitions.values())

    @classmethod
    def execute(cls, db: Session, request: ToolRequest) -> ToolResult:
        definition = cls.get(request.tool_name)
        if definition is None:
            return ToolResult(
                success=False,
                tool_name=request.tool_name,
                answer="Requested deterministic AURIX tool is not registered.",
                limitations=["TOOL_NOT_REGISTERED"],
            )
        if definition.handler is None:
            return ToolResult(
                success=False,
                tool_name=definition.name,
                capability=definition.capability,
                answer="Registered AURIX tool has no executable handler.",
                limitations=["TOOL_HANDLER_UNAVAILABLE"],
            )
        try:
            return definition.handler(db, request)
        except Exception as exc:
            logger.exception(f"Unhandled failure in tool handler {definition.name}")
            return ToolResult(
                success=False,
                tool_name=definition.name,
                capability=definition.capability,
                answer=f"Tool execution failed unexpectedly: {exc}",
                limitations=["TOOL_EXECUTION_ERROR"],
            )


def _register_defaults() -> None:
    if ToolRegistry.get("inventory.position") is not None:
        return

    ToolRegistry.register(
        ToolDefinition(
            name="inventory.position",
            description="Read canonical on-hand and on-order inventory by SKU.",
            capability="INVENTORY_POSITION_RISK",
            domains=[Domain.INVENTORY.value],
            query_types=["READ"],
            requires_entity=True,
            handler=_inventory_position,
        )
    )
    ToolRegistry.register(
        ToolDefinition(
            name="inventory.replenishment_policy",
            description="Read the latest deterministic replenishment policy by SKU.",
            capability="SAFETY_STOCK_ROP",
            domains=[Domain.INVENTORY.value],
            query_types=["READ"],
            requires_entity=True,
            handler=_inventory_policy,
        )
    )
    ToolRegistry.register(
        ToolDefinition(
            name="forecast.latest",
            description="Read the latest completed deterministic forecast for a SKU.",
            capability="DEMAND_FORECASTING",
            domains=[Domain.FORECASTING.value],
            query_types=["READ"],
            requires_entity=True,
            handler=_latest_forecast,
        )
    )
    ToolRegistry.register(
        ToolDefinition(
            name="supplier.performance",
            description="Read the latest supplier performance and risk record.",
            capability="SUPPLIER_PERFORMANCE_RISK",
            domains=[Domain.SUPPLY.value],
            query_types=["READ"],
            requires_entity=True,
            handler=_supplier_performance,
        )
    )
    ToolRegistry.register(
        ToolDefinition(
            name="logistics.shipment",
            description="Read the latest shipment ETA, delay and risk evaluation.",
            capability="SHIPMENT_TRACKING_ETA",
            domains=[Domain.LOGISTICS.value],
            query_types=["READ"],
            requires_entity=True,
            handler=_logistics_shipment,
        )
    )
    ToolRegistry.register(
        ToolDefinition(
            name="phase16.atp",
            description="Calculate deterministic available-to-promise quantity from canonical inventory and reservations.",
            capability="PHASE16_ATP",
            domains=[Domain.DECISION.value],
            query_types=["CALCULATE"],
            requires_entity=True,
            handler=_phase16_atp,
        )
    )
    ToolRegistry.register(
        ToolDefinition(
            name="phase16.ctp",
            description="Calculate deterministic capable-to-promise feasibility using ATP, BOM components, lead time, and optional capacity constraints.",
            capability="PHASE16_CTP",
            domains=[Domain.DECISION.value],
            query_types=["CALCULATE"],
            requires_entity=True,
            handler=_phase16_ctp,
        )
    )
    ToolRegistry.register(
        ToolDefinition(
            name="phase16.mrp",
            description="Calculate deterministic net material requirements from supplied gross requirements and inventory state.",
            capability="PHASE16_MRP",
            domains=[Domain.DECISION.value],
            query_types=["CALCULATE"],
            requires_entity=False,
            handler=_phase16_mrp,
        )
    )
    ToolRegistry.register(
        ToolDefinition(
            name="phase16.capacity",
            description="Check finite resource capacity deterministically and report shortages.",
            capability="PHASE16_CAPACITY",
            domains=[Domain.DECISION.value],
            query_types=["CALCULATE"],
            requires_entity=False,
            handler=_phase16_capacity,
        )
    )
    ToolRegistry.register(
        ToolDefinition(
            name="phase16.scenario",
            description="Run explicit, deterministic Phase 16 what-if scenarios.",
            capability="PHASE16_SCENARIO",
            domains=[Domain.DECISION.value, Domain.ECONOMICS.value],
            query_types=["CALCULATE"],
            requires_entity=False,
            handler=_phase16_scenario,
        )
    )
    ToolRegistry.register(
        ToolDefinition(
            name="phase16.scenario_compare",
            description="Compare explicit deterministic Phase 16 what-if scenarios without inventing an optimization objective.",
            capability="PHASE16_SCENARIO_COMPARE",
            domains=[Domain.DECISION.value, Domain.ECONOMICS.value],
            query_types=["COMPARE"],
            requires_entity=False,
            handler=_phase16_scenario_compare,
        )
    )
    ToolRegistry.register(
        ToolDefinition(
            name="economics.baseline",
            description="Read the latest persisted financial baseline and working-capital metrics.",
            capability="WORKING_CAPITAL_TCO",
            domains=[Domain.ECONOMICS.value],
            query_types=["READ", "ANALYZE"],
            requires_entity=False,
            handler=_financial_baseline,
        )
    )
    ToolRegistry.register(
        ToolDefinition(
            name="intelligence.snapshot",
            description="Read the latest persisted tenant intelligence snapshot.",
            capability="PORTFOLIO_SNAPSHOT",
            domains=[d.value for d in Domain],
            query_types=["READ"],
            requires_entity=False,
            handler=_intelligence_snapshot,
        )
    )


_register_defaults()