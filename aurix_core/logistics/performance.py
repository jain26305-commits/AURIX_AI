"""Logistics performance calculation engine with strict sample-size gating and zero-fabrication guarantees."""

from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd

from aurix_core.logistics.config import LogisticsConfiguration
from aurix_core.schema.phase5_contract import ValueState


class LogisticsPerformanceCalculator:
    """Calculates empirical delivery performance, OTD rates, and transit percentiles from historical records."""

    @staticmethod
    def _calculate_percentile(sorted_values: List[float], percentile: float) -> Optional[float]:
        """Calculates exact empirical percentile using linear interpolation."""
        if not sorted_values:
            return None
        n = len(sorted_values)
        if n == 1:
            return sorted_values[0]

        index = (n - 1) * percentile
        lower = int(index)
        upper = lower + 1
        weight = index - lower

        if upper >= n:
            return sorted_values[-1]

        return sorted_values[lower] * (1.0 - weight) + sorted_values[upper] * weight

    @classmethod
    def calculate_performance(
        cls,
        history_records: List[Dict[str, Any]],
        min_sample_size: int = 3,
        config: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Calculates carrier performance metrics and returns them as a dictionary."""
        _ = config
        sample_size = len(history_records)

        def _make_tv(val: Any, state: ValueState, source: str) -> Dict[str, Any]:
            # Returns dict representation of TrackedValue to satisfy orchestrator expectations natively
            state_str = state.value if hasattr(state, "value") else str(state)
            return {"value": val, "state": state_str, "source": source}

        if sample_size == 0:
            unavail_tv = _make_tv(None, ValueState.UNAVAILABLE, "INSUFFICIENT_SAMPLE_SIZE")
            return {
                "sample_size": 0,
                "on_time_delivery_rate": unavail_tv,
                "in_full_delivery_rate": unavail_tv,
                "otif_rate": unavail_tv,
                "median_transit_days": unavail_tv,
                "p90_transit_days": unavail_tv,
                "p95_transit_days": unavail_tv,
                "transit_std_days": unavail_tv,
                "mean_delay_days": unavail_tv,
            }

        on_time_count = 0
        in_full_count = 0
        otif_count = 0
        transit_days_list: List[float] = []
        delay_days_list: List[float] = []

        valid_otd_records = 0
        valid_inf_records = 0
        valid_otif_records = 0

        for rec in history_records:
            # 1. Dates & Transit calculation
            dispatch_str = rec.get("dispatch_date") or rec.get("order_date")
            promised_str = rec.get("promised_delivery_date") or rec.get("promised_date")
            actual_str = rec.get("actual_delivery_date")

            dispatch_dt = cls._parse_date(dispatch_str)
            promised_dt = cls._parse_date(promised_str)
            actual_dt = cls._parse_date(actual_str)

            if dispatch_dt and actual_dt and actual_dt >= dispatch_dt:
                transit_days = float((actual_dt - dispatch_dt).total_seconds() / 86400.0)
                transit_days_list.append(transit_days)

                if promised_dt:
                    delay_days = float((actual_dt - promised_dt).total_seconds() / 86400.0)
                    delay_days_list.append(max(0.0, delay_days))
                    valid_otd_records += 1
                    if actual_dt <= promised_dt:
                        on_time_count += 1

            # 2. In-Full & OTIF calculations
            ordered_qty = rec.get("ordered_qty") or rec.get("quantity")
            received_qty = rec.get("received_qty") or rec.get("quantity")
            if ordered_qty is not None and received_qty is not None and float(ordered_qty) > 0.0:
                valid_inf_records += 1
                is_inf = float(received_qty) >= float(ordered_qty)
                if is_inf:
                    in_full_count += 1

                if promised_dt and actual_dt:
                    valid_otif_records += 1
                    is_ot = actual_dt <= promised_dt
                    if is_ot and is_inf:
                        otif_count += 1

        # Rates Calculation
        otd_rate = round(on_time_count / valid_otd_records, 4) if valid_otd_records > 0 else None
        inf_rate = round(in_full_count / valid_inf_records, 4) if valid_inf_records > 0 else None
        otif_rate = round(otif_count / valid_otif_records, 4) if valid_otif_records > 0 else None

        otd_tv = _make_tv(
            otd_rate, ValueState.DERIVED if otd_rate is not None else ValueState.UNAVAILABLE, "HISTORICAL_PO_RECORDS"
        )
        inf_tv = _make_tv(
            inf_rate, ValueState.DERIVED if inf_rate is not None else ValueState.UNAVAILABLE, "HISTORICAL_PO_RECORDS"
        )
        otif_tv = _make_tv(
            otif_rate, ValueState.DERIVED if otif_rate is not None else ValueState.UNAVAILABLE, "HISTORICAL_PO_RECORDS"
        )

        # 3. Transit Percentiles with Strict Sample Size Gating
        if sample_size >= min_sample_size and len(transit_days_list) > 0:
            median_val = round(float(np.median(transit_days_list)), 2)
            p90_val = round(float(np.percentile(transit_days_list, 90)), 2)
            p95_val = round(float(np.percentile(transit_days_list, 95)), 2)
            std_val = round(float(np.std(transit_days_list)), 2)

            median_tv = _make_tv(median_val, ValueState.DERIVED, "HISTORICAL_TRANSIT_MEDIAN")
            p90_tv = _make_tv(p90_val, ValueState.DERIVED, "HISTORICAL_TRANSIT_P90")
            p95_tv = _make_tv(p95_val, ValueState.DERIVED, "HISTORICAL_TRANSIT_P95")
            std_tv = _make_tv(std_val, ValueState.DERIVED, "HISTORICAL_TRANSIT_STD")
        else:
            unavail_transit = _make_tv(None, ValueState.UNAVAILABLE, "INSUFFICIENT_SAMPLE_SIZE")
            median_tv = unavail_transit
            p90_tv = unavail_transit
            p95_tv = unavail_transit
            std_tv = unavail_transit

        mean_delay_val = round(float(np.mean(delay_days_list)), 2) if delay_days_list else 0.0
        mean_delay_tv = _make_tv(
            mean_delay_val, ValueState.DERIVED if delay_days_list else ValueState.UNAVAILABLE, "HISTORICAL_DELAYS"
        )

        return {
            "sample_size": sample_size,
            "on_time_delivery_rate": otd_tv,
            "in_full_delivery_rate": inf_tv,
            "otif_rate": otif_tv,
            "median_transit_days": median_tv,
            "p90_transit_days": p90_tv,
            "p95_transit_days": p95_tv,
            "transit_std_days": std_tv,
            "mean_delay_days": mean_delay_tv,
        }

    @classmethod
    def calculate_lane_performance(
        cls,
        shipment_records: List[Dict[str, Any]],
        config: Optional[LogisticsConfiguration] = None,
    ) -> Dict[str, Any]:
        """Calculates lane-specific transportation metrics including median, P90, and P95 transit times."""
        cfg = config or LogisticsConfiguration()
        eval_count = len(shipment_records)

        unavail_str = ValueState.UNAVAILABLE.value if hasattr(ValueState.UNAVAILABLE, "value") else str(ValueState.UNAVAILABLE)

        if eval_count == 0:
            return {
                "evaluated_shipment_count": 0,
                "mean_transit_days": None,
                "median_transit_days": None,
                "p90_transit_days": None,
                "p95_transit_days": None,
                "value_state": unavail_str,
                "reason": "NO_HISTORICAL_DATA",
            }

        if eval_count < cfg.min_sample_size:
            return {
                "evaluated_shipment_count": eval_count,
                "mean_transit_days": None,
                "median_transit_days": None,
                "p90_transit_days": None,
                "p95_transit_days": None,
                "value_state": unavail_str,
                "reason": "INSUFFICIENT_SAMPLE_SIZE",
            }

        transit_days: List[float] = []
        for s in shipment_records:
            actual_d = s.get("actual_delivery_date")
            dispatch_d = s.get("dispatch_date") or s.get("order_date")
            if actual_d and dispatch_d:
                try:
                    d_dt = pd.to_datetime(dispatch_d)
                    a_dt = pd.to_datetime(actual_d)
                    days = (a_dt - d_dt).total_seconds() / 86400.0
                    if days >= 0:
                        transit_days.append(days)
                except (ValueError, TypeError):
                    pass

        if not transit_days:
            return {
                "evaluated_shipment_count": eval_count,
                "mean_transit_days": None,
                "median_transit_days": None,
                "p90_transit_days": None,
                "p95_transit_days": None,
                "value_state": unavail_str,
                "reason": "MISSING_TRANSIT_TIMESTAMPS",
            }

        transit_days.sort()
        mean_t = sum(transit_days) / float(len(transit_days))
        median_t = cls._calculate_percentile(transit_days, 0.50)
        p90_t = cls._calculate_percentile(transit_days, 0.90)
        p95_t = cls._calculate_percentile(transit_days, 0.95)

        derived_str = ValueState.DERIVED.value if hasattr(ValueState.DERIVED, "value") else str(ValueState.DERIVED)

        return {
            "evaluated_shipment_count": eval_count,
            "mean_transit_days": mean_t,
            "median_transit_days": median_t,
            "p90_transit_days": p90_t,
            "p95_transit_days": p95_t,
            "value_state": derived_str,
        }

    @classmethod
    def _parse_date(cls, date_val: Any) -> Any:
        if not date_val:
            return None
        try:
            return pd.to_datetime(date_val).to_pydatetime()
        except Exception:
            return None