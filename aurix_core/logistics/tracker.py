"""Shipment tracking and ETA evaluation engine with strict zero-fabrication guarantees."""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple
from aurix_core.schema.phase5_contract import TrackedValue, ValueState
from aurix_core.schema.phase7_contract import (
    CostBreakdown,
    ETADetails,
    EvidenceQuality,
    ShipmentStatus,
    TransportDetails,
)


class ShipmentTracker:
    """Evaluates active shipment status, transit evidence, ETA provenance, and unit economics."""

    @classmethod
    def evaluate_shipment(
        cls,
        shipment_dict: Dict[str, Any],
        historical_median_transit: Optional[float] = None,
        historical_lane_median_transit: Optional[float] = None,
        config: Optional[Any] = None,
    ) -> Tuple[ShipmentStatus, TransportDetails, ETADetails, CostBreakdown]:
        _ = config  # Reserved for config-driven thresholds if needed

        shipment_id = str(shipment_dict.get("shipment_id", "UNKNOWN"))
        carrier_id = shipment_dict.get("carrier_id")
        origin = shipment_dict.get("origin")
        destination = shipment_dict.get("destination")
        transport_mode = shipment_dict.get("transport_mode")

        dispatch_date_str = shipment_dict.get("dispatch_date")
        promised_date_str = shipment_dict.get("promised_date")
        actual_delivery_date_str = shipment_dict.get("actual_delivery_date")

        planned_transit_days = shipment_dict.get("planned_transit_days")
        user_transit_days = shipment_dict.get("transit_days")

        quantity = shipment_dict.get("quantity")
        weight_kg = shipment_dict.get("weight_kg")
        freight_cost = shipment_dict.get("freight_cost")
        currency = str(shipment_dict.get("currency", "USD"))

        now = datetime.now()

        # Parse Dates safely
        dispatch_dt = cls._parse_date(dispatch_date_str)
        promised_dt = cls._parse_date(promised_date_str)
        actual_delivery_dt = cls._parse_date(actual_delivery_date_str)

        # 1. Determine Shipment Status
        if actual_delivery_dt:
            status = ShipmentStatus.DELIVERED
        elif dispatch_dt and promised_dt and now > promised_dt:
            status = ShipmentStatus.DELAYED
        elif dispatch_dt:
            status = ShipmentStatus.IN_TRANSIT
        else:
            status = ShipmentStatus.NOT_DISPATCHED

        # 2. Transport & Distance Details (Zero-Fabrication)
        dist_val = shipment_dict.get("distance_km")
        if dist_val is not None and float(dist_val) > 0.0:
            distance_obj = TrackedValue(
                value=float(dist_val),
                state=ValueState.OBSERVED,
                source="SHIPMENT_RECORD",
            )
        else:
            distance_obj = TrackedValue(
                value=None,
                state=ValueState.UNAVAILABLE,
                source="DISTANCE_UNAVAILABLE",
            )

        transport_details = TransportDetails(
            carrier_id=carrier_id,
            mode=transport_mode,
            origin=origin,
            destination=destination,
            distance_km=distance_obj,
        )

        # 3. Cost Breakdown Calculations (Zero-Division & Negative Safety)
        qty_val = float(quantity) if (quantity is not None and float(quantity) > 0.0) else None
        wt_val = float(weight_kg) if (weight_kg is not None and float(weight_kg) > 0.0) else None
        cost_val = float(freight_cost) if (freight_cost is not None and float(freight_cost) >= 0.0) else None

        cost_per_unit_obj = TrackedValue(
            value=(
                round(cost_val / qty_val, 2)
                if (cost_val is not None and qty_val is not None and qty_val > 0.0)
                else None
            ),
            state=(
                ValueState.DERIVED
                if (cost_val is not None and qty_val is not None and qty_val > 0.0)
                else ValueState.UNAVAILABLE
            ),
            source=(
                "FREIGHT_COST_DIV_QTY"
                if (cost_val is not None and qty_val is not None and qty_val > 0.0)
                else "UNAVAILABLE"
            ),
        )

        cost_per_kg_obj = TrackedValue(
            value=(
                round(cost_val / wt_val, 2) if (cost_val is not None and wt_val is not None and wt_val > 0.0) else None
            ),
            state=(
                ValueState.DERIVED
                if (cost_val is not None and wt_val is not None and wt_val > 0.0)
                else ValueState.UNAVAILABLE
            ),
            source=(
                "FREIGHT_COST_DIV_WEIGHT"
                if (cost_val is not None and wt_val is not None and wt_val > 0.0)
                else "UNAVAILABLE"
            ),
        )

        total_freight_cost_obj = TrackedValue(
            value=cost_val,
            state=ValueState.OBSERVED if cost_val is not None else ValueState.UNAVAILABLE,
            source="SHIPMENT_RECORD" if cost_val is not None else "UNAVAILABLE",
        )

        cost_breakdown = CostBreakdown(
            total_freight_cost=total_freight_cost_obj,
            cost_per_unit=cost_per_unit_obj,
            cost_per_kg=cost_per_kg_obj,
            currency=currency,
        )

        # 4. Deterministic ETA Evidence Hierarchy & Precedence
        eta_date, eta_source, eta_method, evidence_quality, sample_size = cls._resolve_eta(
            actual_delivery_dt=actual_delivery_dt,
            dispatch_dt=dispatch_dt,
            historical_lane_median=historical_lane_median_transit,
            historical_carrier_median=historical_median_transit,
            planned_transit_days=planned_transit_days,
            user_transit_days=user_transit_days,
        )

        eta_details = ETADetails(
            estimated_delivery_date=eta_date.strftime("%Y-%m-%d") if eta_date else None,
            value_state=(
                ValueState.OBSERVED
                if actual_delivery_dt
                else (ValueState.INFERRED if eta_date else ValueState.UNAVAILABLE)
            ),
            eta_source=eta_source,
            eta_method=eta_method,
            evidence_quality=evidence_quality,
            supporting_sample_size=sample_size,
            provenance={
                "shipment_id": shipment_id,
                "dispatch_date": dispatch_date_str,
                "promised_date": promised_date_str,
                "engine_version": "6.0.0-hardened",
            },
        )

        return status, transport_details, eta_details, cost_breakdown

    @classmethod
    def _parse_date(cls, date_val: Any) -> Optional[datetime]:
        if not date_val:
            return None
        if isinstance(date_val, datetime):
            return date_val
        if isinstance(date_val, str):
            try:
                return datetime.fromisoformat(date_val.replace("Z", ""))
            except ValueError:
                try:
                    return datetime.strptime(date_val.split("T")[0], "%Y-%m-%d")
                except ValueError:
                    return None
        return None

    @classmethod
    def _resolve_eta(
        cls,
        actual_delivery_dt: Optional[datetime],
        dispatch_dt: Optional[datetime],
        historical_lane_median: Optional[float],
        historical_carrier_median: Optional[float],
        planned_transit_days: Optional[Any],
        user_transit_days: Optional[Any],
    ) -> Tuple[Optional[datetime], str, str, EvidenceQuality, Optional[int]]:
        """
        Deterministic ETA Precedence Hierarchy:
        1. Actual delivery date (OBSERVED) -> HIGH
        2. Historical carrier lane median (INFERRED) -> HIGH (if sample size met)
        3. Historical carrier median (INFERRED) -> MEDIUM
        4. Planned / contracted transit (OBSERVED / USER_PROVIDED) -> MEDIUM
        5. User-provided transit (USER_PROVIDED) -> LOW
        6. UNAVAILABLE -> UNAVAILABLE
        """
        # Precedence 1: Actual Delivery Date
        if actual_delivery_dt:
            return actual_delivery_dt, "ACTUAL_DELIVERY_DATE", "OBSERVED_DELIVERY", EvidenceQuality.HIGH, None

        # Precedence 2: Historical Carrier Lane Median
        if dispatch_dt and historical_lane_median is not None and float(historical_lane_median) > 0.0:
            eta = dispatch_dt + timedelta(days=float(historical_lane_median))
            return eta, "HISTORICAL_CARRIER_LANE_MEDIAN", "LANE_MEDIAN_TRANSIT", EvidenceQuality.HIGH, None

        # Precedence 3: Historical Carrier Median
        if dispatch_dt and historical_carrier_median is not None and float(historical_carrier_median) > 0.0:
            eta = dispatch_dt + timedelta(days=float(historical_carrier_median))
            return eta, "HISTORICAL_CARRIER_MEDIAN", "CARRIER_MEDIAN_TRANSIT", EvidenceQuality.MEDIUM, None

        # Precedence 4: Planned or Contracted Transit Days
        if dispatch_dt and planned_transit_days is not None and float(planned_transit_days) > 0.0:
            eta = dispatch_dt + timedelta(days=float(planned_transit_days))
            return eta, "PLANNED_OR_CONTRACTED_TRANSIT", "PLANNED_TRANSIT", EvidenceQuality.MEDIUM, None

        # Precedence 5: User Provided Transit Days
        if dispatch_dt and user_transit_days is not None and float(user_transit_days) > 0.0:
            eta = dispatch_dt + timedelta(days=float(user_transit_days))
            return eta, "USER_PROVIDED_TRANSIT", "USER_TRANSIT", EvidenceQuality.LOW, None

        # Fallback: No Valid Evidence Exists -> UNAVAILABLE (Zero Fabrication)
        return None, "UNAVAILABLE", "INSUFFICIENT_TRANSIT_EVIDENCE", EvidenceQuality.UNAVAILABLE, None
