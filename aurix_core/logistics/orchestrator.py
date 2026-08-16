"""Phase 6 Logistics Intelligence analytical orchestrator coordinating calculation modules."""

from typing import Any, Dict, List, Optional
import pandas as pd

from aurix_core.logistics.config import LogisticsConfiguration
from aurix_core.logistics.eta_engine import DeterministicETAEngine
from aurix_core.logistics.performance import LogisticsPerformanceCalculator
from aurix_core.logistics.risk_consequence import (
    FreightEconomicsCalculator,
    InventoryConsequenceEngine,
    LogisticsRiskEvaluator,
)
from aurix_core.schema.phase5_contract import ValueState


class Phase6Orchestrator:
    """
    Coordinates historical performance calculations, deterministic ETA estimations,
    freight unit economics, and inventory coverage risk/expedite evaluation.
    """

    def __init__(
        self,
        payload: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.payload = payload
        self._raw_config = config or {}
        self.config = LogisticsConfiguration(self._raw_config)

    def execute(self) -> Dict[str, Any]:
        """
        Executes full analytical logistics pipeline and builds structured engine output.
        """
        # 1. Historical Carrier Performance
        carrier_records_map = self.payload.get("carrier_history", {})
        carrier_performances: List[Dict[str, Any]] = []
        carrier_perf_by_id: Dict[str, Dict[str, Any]] = {}

        for carrier_id, records in carrier_records_map.items():
            perf_dict = LogisticsPerformanceCalculator.calculate_performance(
                history_records=records,
                min_sample_size=self.config.min_sample_size,
                config=self.config,
            )

            # Extract metrics defensively for risk scoring
            otd_val = None
            if "on_time_delivery_rate" in perf_dict:
                otd_obj = perf_dict["on_time_delivery_rate"]
                if isinstance(otd_obj, dict):
                    otd_val = otd_obj.get("value")

            std_val = None
            if "transit_std_days" in perf_dict:
                std_obj = perf_dict["transit_std_days"]
                if isinstance(std_obj, dict):
                    std_val = std_obj.get("value")

            risk_res = LogisticsRiskEvaluator.evaluate_risk(
                delay_days=0.0,
                carrier_otd_rate=otd_val,
                transit_std_days=std_val,
                inventory_coverage_days=None,
                config=self.config,
            )

            inf_obj = perf_dict.get("in_full_delivery_rate", {})
            inf_val = inf_obj.get("value") if isinstance(inf_obj, dict) else None

            otif_obj = perf_dict.get("otif_rate", {})
            otif_val = otif_obj.get("value") if isinstance(otif_obj, dict) else None

            med_obj = perf_dict.get("median_transit_days", {})
            med_val = med_obj.get("value") if isinstance(med_obj, dict) else None

            r_level = risk_res["risk_level"]
            risk_level_str = r_level.value if hasattr(r_level, "value") else str(r_level)

            perf_entry = {
                "carrier_id": str(carrier_id),
                "evaluated_order_count": perf_dict.get("sample_size", len(records)),
                "otd_rate": otd_val,
                "in_full_rate": inf_val,
                "otif_rate": otif_val,
                "median_transit_days": med_val,
                "transit_std_days": std_val,
                "risk_score": risk_res["risk_score"],
                "risk_level": risk_level_str,
                "risk_drivers": risk_res["risk_drivers"],
            }
            carrier_performances.append(perf_entry)
            carrier_perf_by_id[str(carrier_id)] = perf_entry

        # 2. Historical Lane Performance
        lane_records_map = self.payload.get("lane_history", {})
        lane_performances: List[Dict[str, Any]] = []
        lane_perf_by_key: Dict[str, Dict[str, Any]] = {}

        for lane_key, records in lane_records_map.items():
            parts = str(lane_key).split("->")
            origin_id = parts[0] if len(parts) > 0 else "UNKNOWN_ORIGIN"
            dest_id = parts[1] if len(parts) > 1 else "UNKNOWN_DESTINATION"
            carrier_id = parts[2] if len(parts) > 2 else None

            lane_perf = LogisticsPerformanceCalculator.calculate_lane_performance(
                shipment_records=records,
                config=self.config,
            )

            lane_entry = {
                "origin_id": origin_id,
                "destination_id": dest_id,
                "carrier_id": carrier_id,
                "evaluated_shipment_count": lane_perf.get("evaluated_shipment_count", 0),
                "mean_transit_days": lane_perf.get("mean_transit_days"),
                "median_transit_days": lane_perf.get("median_transit_days"),
                "p90_transit_days": lane_perf.get("p90_transit_days"),
                "p95_transit_days": lane_perf.get("p95_transit_days"),
            }
            lane_performances.append(lane_entry)
            lane_perf_by_key[str(lane_key)] = lane_entry

        # 3. Active Shipment Evaluations
        active_shipments = self.payload.get("shipments", [])
        inventory_coverage_map = self.payload.get("inventory_coverage", {})
        shipment_evaluations: List[Dict[str, Any]] = []

        # Extract delay buffer safely from raw config
        delay_buffer = float(self._raw_config.get("delay_buffer_hours", 0.0))

        for ship in active_shipments:
            ship_id = str(ship.get("shipment_id", "UNKNOWN_SHIPMENT"))
            c_id = str(ship.get("carrier_id")) if ship.get("carrier_id") else None
            sku_id = str(ship.get("sku_id")) if ship.get("sku_id") else None
            orig_id = str(ship.get("origin_id", ""))
            dest_id = str(ship.get("destination_id", ""))

            # Lookup Carrier & Lane Performance
            c_perf = carrier_perf_by_id.get(c_id) if c_id else None

            lane_key = f"{orig_id}->{dest_id}"
            if c_id:
                lane_key_full = f"{orig_id}->{dest_id}->{c_id}"
                l_perf = lane_perf_by_key.get(lane_key_full) or lane_perf_by_key.get(lane_key)
            else:
                l_perf = lane_perf_by_key.get(lane_key)

            # ETA Calculation
            eta_res = DeterministicETAEngine.calculate_eta(
                shipment=ship,
                carrier_performance=c_perf,
                lane_performance=l_perf,
            )

            est_delivery = eta_res.get("estimated_delivery_date")
            promised_delivery = ship.get("promised_delivery_date")

            # Delay Calculation
            delay_hours = 0.0
            delay_days = 0.0
            is_delayed = False

            if est_delivery and promised_delivery:
                try:
                    p_dt = pd.to_datetime(promised_delivery).to_pydatetime()
                    if est_delivery > p_dt:
                        diff_seconds = (est_delivery - p_dt).total_seconds()
                        delay_hours = round(diff_seconds / 3600.0, 2)
                        delay_days = round(diff_seconds / 86400.0, 2)
                        if delay_hours > delay_buffer:
                            is_delayed = True
                except Exception:
                    pass

            # Inventory Coverage Lookup
            cov_days = inventory_coverage_map.get(sku_id) if sku_id else None

            # Expedite Decision Engine
            expedite_res = InventoryConsequenceEngine.evaluate_expedite_decision(
                delay_days=delay_days,
                inventory_coverage_days=cov_days,
                config=self.config,
            )

            # Freight Unit Economics
            freight_res = FreightEconomicsCalculator.calculate_freight_economics(
                freight_cost=ship.get("freight_cost"),
                quantity=ship.get("quantity"),
                weight_kg=ship.get("weight_kg"),
                currency=ship.get("currency"),
            )

            # Overall Logistics Risk Scoring
            c_otd = c_perf.get("otd_rate") if c_perf else None
            c_std = c_perf.get("transit_std_days") if c_perf else None

            ship_risk = LogisticsRiskEvaluator.evaluate_risk(
                delay_days=delay_days,
                carrier_otd_rate=c_otd,
                transit_std_days=c_std,
                inventory_coverage_days=cov_days,
                config=self.config,
            )

            s_r_level = ship_risk["risk_level"]
            s_risk_str = s_r_level.value if hasattr(s_r_level, "value") else str(s_r_level)

            v_state = eta_res.get("value_state")
            if not v_state:
                v_state = ValueState.DERIVED.value if hasattr(ValueState.DERIVED, "value") else str(ValueState.DERIVED)

            est_del_str = (
                est_delivery.isoformat()
                if est_delivery is not None and hasattr(est_delivery, "isoformat")
                else (str(est_delivery) if est_delivery is not None else None)
            )

            ship_eval = {
                "shipment_id": ship_id,
                "order_id": ship.get("order_id"),
                "sku_id": sku_id,
                "carrier_id": c_id,
                "origin_id": orig_id,
                "destination_id": dest_id,
                "quantity": ship.get("quantity"),
                "weight_kg": ship.get("weight_kg"),
                "dispatch_date": ship.get("dispatch_date"),
                "promised_delivery_date": promised_delivery,
                "estimated_delivery_date": est_del_str,
                "actual_delivery_date": ship.get("actual_delivery_date"),
                "eta_source": eta_res.get("eta_source"),
                "delay_hours": delay_hours,
                "is_delayed": is_delayed,
                "logistics_risk_score": ship_risk["risk_score"],
                "risk_level": s_risk_str,
                "expedite_recommendation": expedite_res["expedite_recommendation"],
                "recommendation_reason": expedite_res["recommendation_reason"],
                "freight_cost": freight_res["freight_cost"],
                "cost_per_unit": freight_res["cost_per_unit"],
                "cost_per_kg": freight_res["cost_per_kg"],
                "currency": freight_res["currency"],
                "value_state": str(v_state),
            }
            shipment_evaluations.append(ship_eval)

        return {
            "carrier_performances": carrier_performances,
            "lane_performances": lane_performances,
            "shipment_evaluations": shipment_evaluations,
            "provenance": {
                "engine": "Phase6Orchestrator",
                "evaluated_carriers": len(carrier_performances),
                "evaluated_lanes": len(lane_performances),
                "evaluated_shipments": len(shipment_evaluations),
            },
        }