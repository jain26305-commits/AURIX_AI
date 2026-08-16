"""Deterministic ETA calculation engine enforcing 6-tier evidence precedence and Zero-Fabrication."""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from aurix_core.schema.phase5_contract import TrackedValue, ValueState


class DeterministicETAEngine:
    """
    Calculates estimated time of arrival (ETA) using strict evidence precedence.

    6-Tier Deterministic Precedence Hierarchy:
    1. Actual Delivery Date (Observed Fact)
    2. Historical Carrier + Lane Median Transit (High Empirical)
    3. Historical Carrier Median Transit (Moderate Empirical)
    4. Explicit Planned / Contracted Transit (Contractual Baseline)
    5. Explicit User-Provided Transit (User Estimate)
    6. No Evidence -> ValueState.UNAVAILABLE (Zero Fabrication)
    """

    @classmethod
    def calculate_eta(
        cls,
        shipment: Dict[str, Any],
        carrier_performance: Optional[Dict[str, Any]] = None,
        lane_performance: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Calculates the estimated delivery date and returns complete provenance and evidence metadata.
        """
        actual_d = cls._parse_date(shipment.get("actual_delivery_date"))
        dispatch_d = cls._parse_date(shipment.get("dispatch_date"))

        # Tier 1: Actual Delivery Date (Observed Fact)
        if actual_d is not None:
            return {
                "estimated_delivery_date": actual_d,
                "eta_source": "ACTUAL_DELIVERY",
                "eta_method": "OBSERVED_FACT",
                "evidence_quality": "HIGH_OBSERVED",
                "supporting_sample_size": 1,
                "value_state": ValueState.DERIVED.value,
                "tracked_value": TrackedValue(
                    value=actual_d.isoformat(),
                    state=ValueState.OBSERVED,
                    source="ACTUAL_DELIVERY_RECORD",
                ),
            }

        if dispatch_d is None:
            return cls._build_unavailable_response("MISSING_DISPATCH_DATE")

        # Tier 2: Historical Carrier + Lane Median Transit
        if lane_performance is not None:
            lane_median = cls._extract_metric_value(lane_performance, "median_transit_days")
            sample_size = cls._extract_sample_size(lane_performance, "evaluated_shipment_count")
            if lane_median is not None and lane_median >= 0.0:
                eta_date = dispatch_d + timedelta(days=float(lane_median))
                return {
                    "estimated_delivery_date": eta_date,
                    "eta_source": "HISTORICAL_LANE_CARRIER_MEDIAN",
                    "eta_method": "MEDIAN_TRANSIT_INTERPOLATION",
                    "evidence_quality": "HIGH_EMPIRICAL",
                    "supporting_sample_size": sample_size,
                    "value_state": ValueState.DERIVED.value,
                    "tracked_value": TrackedValue(
                        value=eta_date.isoformat(),
                        state=ValueState.DERIVED,
                        source="HISTORICAL_LANE_CARRIER_MEDIAN",
                    ),
                }

        # Tier 3: Historical Carrier Median Transit
        if carrier_performance is not None:
            carrier_median = cls._extract_metric_value(
                carrier_performance, "median_transit_days"
            ) or cls._extract_metric_value(carrier_performance, "mean_transit_days")
            sample_size = cls._extract_sample_size(carrier_performance, "sample_size") or cls._extract_sample_size(
                carrier_performance, "evaluated_order_count"
            )
            if carrier_median is not None and carrier_median >= 0.0:
                eta_date = dispatch_d + timedelta(days=float(carrier_median))
                return {
                    "estimated_delivery_date": eta_date,
                    "eta_source": "HISTORICAL_CARRIER_MEDIAN",
                    "eta_method": "CARRIER_TRANSIT_INTERPOLATION",
                    "evidence_quality": "MODERATE_EMPIRICAL",
                    "supporting_sample_size": sample_size,
                    "value_state": ValueState.DERIVED.value,
                    "tracked_value": TrackedValue(
                        value=eta_date.isoformat(),
                        state=ValueState.DERIVED,
                        source="HISTORICAL_CARRIER_MEDIAN",
                    ),
                }

        # Tier 4: Explicit Planned / Contracted Transit
        planned_days = shipment.get("planned_transit_days")
        if planned_days is not None:
            try:
                p_float = float(planned_days)
                if p_float >= 0.0:
                    eta_date = dispatch_d + timedelta(days=p_float)
                    return {
                        "estimated_delivery_date": eta_date,
                        "eta_source": "CONTRACTUAL_PLANNED_TRANSIT",
                        "eta_method": "CONTRACT_TRANSIT_ADDITION",
                        "evidence_quality": "CONTRACTUAL_BASELINE",
                        "supporting_sample_size": 1,
                        "value_state": ValueState.DERIVED.value,
                        "tracked_value": TrackedValue(
                            value=eta_date.isoformat(),
                            state=ValueState.OBSERVED,
                            source="PLANNED_TRANSIT_DAYS",
                        ),
                    }
            except (ValueError, TypeError):
                pass

        # Tier 5: Explicit User-Provided Transit
        user_transit = shipment.get("user_provided_transit_days")
        if user_transit is not None:
            try:
                u_float = float(user_transit)
                if u_float >= 0.0:
                    eta_date = dispatch_d + timedelta(days=u_float)
                    return {
                        "estimated_delivery_date": eta_date,
                        "eta_source": "USER_PROVIDED_TRANSIT",
                        "eta_method": "USER_TRANSIT_ADDITION",
                        "evidence_quality": "USER_ESTIMATE",
                        "supporting_sample_size": 1,
                        "value_state": ValueState.DERIVED.value,
                        "tracked_value": TrackedValue(
                            value=eta_date.isoformat(),
                            state=ValueState.OBSERVED,
                            source="USER_PROVIDED_TRANSIT_DAYS",
                        ),
                    }
            except (ValueError, TypeError):
                pass

        # Tier 6: No Evidence -> ValueState.UNAVAILABLE (Zero Fabrication)
        return cls._build_unavailable_response("INSUFFICIENT_TRANSIT_EVIDENCE")

    @classmethod
    def _extract_metric_value(cls, performance_data: Any, key: str) -> Optional[float]:
        """Defensively extracts float metric values from dictionaries, ORMs, or TrackedValue objects."""
        if performance_data is None:
            return None

        val = None
        if isinstance(performance_data, dict):
            val = performance_data.get(key)
        else:
            val = getattr(performance_data, key, None)

        if val is None:
            return None

        # Handle TrackedValue wrapper objects
        if hasattr(val, "value"):
            val = getattr(val, "value")
        if hasattr(val, "state") and getattr(val, "state") == ValueState.UNAVAILABLE:
            return None

        if val is None:
            return None

        try:
            return float(val)
        except (ValueError, TypeError):
            return None

    @classmethod
    def _extract_sample_size(cls, performance_data: Any, key: str) -> int:
        """Defensively extracts integer sample size from dictionary or object."""
        if performance_data is None:
            return 0
        val = performance_data.get(key) if isinstance(performance_data, dict) else getattr(performance_data, key, 0)
        try:
            return int(val) if val is not None else 0
        except (ValueError, TypeError):
            return 0

    @classmethod
    def _build_unavailable_response(cls, reason: str) -> Dict[str, Any]:
        """Builds standardized response for UNAVAILABLE state without fabricating data."""
        return {
            "estimated_delivery_date": None,
            "eta_source": "NONE",
            "eta_method": "UNAVAILABLE",
            "evidence_quality": "UNAVAILABLE",
            "supporting_sample_size": 0,
            "value_state": ValueState.UNAVAILABLE.value,
            "reason": reason,
            "tracked_value": TrackedValue(
                value=None,
                state=ValueState.UNAVAILABLE,
                source=reason,
            ),
        }

    @classmethod
    def _parse_date(cls, date_val: Any) -> Optional[datetime]:
        """Defensively parses datetime or string objects into datetime instances."""
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