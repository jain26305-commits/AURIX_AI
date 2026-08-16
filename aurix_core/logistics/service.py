"""Enterprise logistics intelligence service adapter managing persistence, multi-tenancy, and idempotency."""

import json
import uuid
import hashlib
from typing import Any, Dict, List, Optional
import pandas as pd
from sqlalchemy.orm import Session

from aurix_core.config.settings import settings
from aurix_core.database.models.logistics_intelligence import (
    LogisticsIntelligenceRun,
    CarrierPerformance,
    LanePerformance,
    ShipmentEvaluation,
)
from aurix_core.database.repositories.logistics_intelligence import (
    LogisticsIntelligenceRunRepository,
    CarrierPerformanceRepository,
    LanePerformanceRepository,
    ShipmentEvaluationRepository,
)
from aurix_core.logistics.orchestrator import Phase6Orchestrator


class LogisticsIntelligenceService:
    """
    Enterprise service adapter for Phase 6 Logistics Intelligence.
    Orchestrates multi-tenant data persistence, SHA-256 idempotency hashing,
    and transaction-safe database commitments.
    """

    def __init__(self, db: Session, tenant_id: Optional[str] = None) -> None:
        self.db = db
        self.tenant_id = tenant_id or settings.default_tenant_id
        self.run_repo = LogisticsIntelligenceRunRepository(db, self.tenant_id)
        self.carrier_repo = CarrierPerformanceRepository(db, self.tenant_id)
        self.lane_repo = LanePerformanceRepository(db, self.tenant_id)
        self.shipment_repo = ShipmentEvaluationRepository(db, self.tenant_id)

    def _compute_dataset_hash(self, payload: Dict[str, Any], config: Dict[str, Any]) -> str:
        """Computes deterministic SHA-256 hash across canonical inputs and configuration."""
        data_str = json.dumps({"payload": payload, "config": config}, sort_keys=True, default=str)
        return hashlib.sha256(data_str.encode("utf-8")).hexdigest()

    def run_logistics_intelligence(
        self,
        input_payload: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None,
        force_recompute: bool = False,
    ) -> Dict[str, Any]:
        """Executes a logistics intelligence run with idempotency checks and atomic persistence."""
        exec_config = config or {}
        dataset_hash = self._compute_dataset_hash(input_payload, exec_config)

        # 1. Idempotency Check
        if not force_recompute:
            existing_run = self.run_repo.get_by_hash(dataset_hash)
            if existing_run:
                run_id_str = str(getattr(existing_run, "id"))
                existing_carriers = self.carrier_repo.list_by_run_id(run_id_str)
                existing_lanes = self.lane_repo.list_by_run_id(run_id_str)
                existing_shipments = self.shipment_repo.list_by_run_id(run_id_str)
                return {
                    "status": "COMPLETED",
                    "idempotent_hit": True,
                    "logistics_run_id": run_id_str,
                    "dataset_hash": dataset_hash,
                    "carrier_count": len(existing_carriers),
                    "lane_count": len(existing_lanes),
                    "shipment_count": len(existing_shipments),
                    "message": "Returned cached logistics intelligence run for identical inputs.",
                }

        # 2. Generate Run ID & Record Initial State
        run_id = f"P6_RUN_{uuid.uuid4().hex[:12]}"
        run_record = LogisticsIntelligenceRun(
            id=run_id,
            dataset_hash=dataset_hash,
            status="EXECUTING",
            configuration=json.dumps(exec_config),
            tenant_id=self.tenant_id,
        )
        self.run_repo.create(run_record)

        # 3. Execute Analytical Engine
        try:
            orchestrator = Phase6Orchestrator(payload=input_payload, config=exec_config)
            engine_output = orchestrator.execute()

            def _safe_float(val: Any) -> Optional[float]:
                if val is None or pd.isna(val):
                    return None
                try:
                    return float(val)
                except (ValueError, TypeError):
                    return None

            def _safe_int(val: Any, default: int = 0) -> int:
                if val is None or pd.isna(val):
                    return default
                try:
                    return int(val)
                except (ValueError, TypeError):
                    return default

            def _parse_dt_safe(val: Any) -> Optional[Any]:
                if not val:
                    return None
                try:
                    return pd.to_datetime(val).to_pydatetime()
                except Exception:
                    return None

            # Persist Carrier Performance Records
            carriers_data = engine_output.get("carrier_performances", [])
            carrier_records: List[CarrierPerformance] = []
            for carrier_item in carriers_data:
                drivers = carrier_item.get("risk_drivers")
                drivers_str: Optional[str] = None
                if isinstance(drivers, (list, dict)):
                    drivers_str = json.dumps(drivers)
                elif drivers is not None:
                    drivers_str = str(drivers)

                c_rec = CarrierPerformance(
                    run_id=run_id,
                    carrier_id=str(carrier_item.get("carrier_id", "UNKNOWN_CARRIER")),
                    evaluated_order_count=_safe_int(carrier_item.get("evaluated_order_count"), default=0),
                    otd_rate=_safe_float(carrier_item.get("otd_rate")),
                    in_full_rate=_safe_float(carrier_item.get("in_full_rate")),
                    otif_rate=_safe_float(carrier_item.get("otif_rate")),
                    mean_transit_days=_safe_float(carrier_item.get("median_transit_days")),
                    transit_std_days=_safe_float(carrier_item.get("transit_std_days")),
                    risk_score=_safe_float(carrier_item.get("risk_score")),
                    risk_level=carrier_item.get("risk_level", "UNASSESSED"),
                    risk_drivers=drivers_str,
                    tenant_id=self.tenant_id,
                )
                carrier_records.append(c_rec)

            for crec in carrier_records:
                self.carrier_repo.create(crec)

            # Persist Lane Performance Records
            lanes_data = engine_output.get("lane_performances", [])
            lane_records: List[LanePerformance] = []
            for lane_item in lanes_data:
                l_rec = LanePerformance(
                    run_id=run_id,
                    origin_id=str(lane_item.get("origin_id", "UNKNOWN_ORIGIN")),
                    destination_id=str(lane_item.get("destination_id", "UNKNOWN_DESTINATION")),
                    carrier_id=str(lane_item.get("carrier_id")) if lane_item.get("carrier_id") else None,
                    evaluated_shipment_count=_safe_int(lane_item.get("evaluated_shipment_count"), default=0),
                    mean_transit_days=_safe_float(lane_item.get("mean_transit_days")),
                    median_transit_days=_safe_float(lane_item.get("median_transit_days")),
                    p90_transit_days=_safe_float(lane_item.get("p90_transit_days")),
                    p95_transit_days=_safe_float(lane_item.get("p95_transit_days")),
                    tenant_id=self.tenant_id,
                )
                lane_records.append(l_rec)

            for lrec in lane_records:
                self.lane_repo.create(lrec)

            # Persist Shipment Evaluation Records
            shipments_data = engine_output.get("shipment_evaluations", [])
            shipment_records: List[ShipmentEvaluation] = []
            for ship_item in shipments_data:
                s_rec = ShipmentEvaluation(
                    run_id=run_id,
                    shipment_id=str(ship_item.get("shipment_id", "UNKNOWN_SHIPMENT")),
                    order_id=str(ship_item.get("order_id")) if ship_item.get("order_id") else None,
                    sku_id=str(ship_item.get("sku_id")) if ship_item.get("sku_id") else None,
                    carrier_id=str(ship_item.get("carrier_id")) if ship_item.get("carrier_id") else None,
                    origin_id=str(ship_item.get("origin_id")) if ship_item.get("origin_id") else None,
                    destination_id=str(ship_item.get("destination_id")) if ship_item.get("destination_id") else None,
                    quantity=_safe_float(ship_item.get("quantity")),
                    weight_kg=_safe_float(ship_item.get("weight_kg")),
                    dispatch_date=_parse_dt_safe(ship_item.get("dispatch_date")),
                    promised_delivery_date=_parse_dt_safe(ship_item.get("promised_delivery_date")),
                    estimated_delivery_date=_parse_dt_safe(ship_item.get("estimated_delivery_date")),
                    actual_delivery_date=_parse_dt_safe(ship_item.get("actual_delivery_date")),
                    eta_source=ship_item.get("eta_source"),
                    delay_hours=_safe_float(ship_item.get("delay_hours")),
                    is_delayed=bool(ship_item.get("is_delayed", False)),
                    logistics_risk_score=_safe_float(ship_item.get("logistics_risk_score")),
                    risk_level=ship_item.get("risk_level", "UNASSESSED"),
                    expedite_recommendation=ship_item.get("expedite_recommendation", "NORMAL_TRANSPORT"),
                    recommendation_reason=ship_item.get("recommendation_reason"),
                    freight_cost=_safe_float(ship_item.get("freight_cost")),
                    cost_per_unit=_safe_float(ship_item.get("cost_per_unit")),
                    cost_per_kg=_safe_float(ship_item.get("cost_per_kg")),
                    currency=ship_item.get("currency"),
                    value_state=str(ship_item.get("value_state", "DERIVED")),
                    tenant_id=self.tenant_id,
                )
                shipment_records.append(s_rec)

            for srec in shipment_records:
                self.shipment_repo.create(srec)

            # Update Run Status to Completed
            setattr(run_record, "status", "COMPLETED")
            setattr(run_record, "provenance", json.dumps(engine_output.get("provenance", {})))
            self.db.commit()

            return {
                "status": "COMPLETED",
                "idempotent_hit": False,
                "logistics_run_id": run_id,
                "dataset_hash": dataset_hash,
                "carrier_count": len(carrier_records),
                "lane_count": len(lane_records),
                "shipment_count": len(shipment_records),
                "engine_output": engine_output,
            }

        except Exception as e:
            self.db.rollback()
            setattr(run_record, "status", "FAILED")
            setattr(run_record, "provenance", json.dumps({"error": str(e)}))
            self.db.add(run_record)
            self.db.flush()
            self.db.commit()
            return {
                "status": "FAILED",
                "logistics_run_id": run_id,
                "dataset_hash": dataset_hash,
                "error": str(e),
            }