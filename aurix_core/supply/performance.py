import math
from datetime import datetime
from typing import Any, Dict, List, Optional
from aurix_core.schema.phase5_contract import TrackedValue, ValueState
from aurix_core.schema.phase6_contract import SupplierPerformanceMetrics


class SupplierPerformanceCalculator:
    """Calculates historical supplier performance metrics deterministically from purchase order records."""

    @staticmethod
    def _parse_date(date_val: Any) -> Optional[datetime]:
        """Safely parses string or datetime objects into a datetime instance."""
        if date_val is None:
            return None
        if isinstance(date_val, datetime):
            return date_val
        if isinstance(date_val, str):
            clean_str = date_val.strip()
            if not clean_str:
                return None
            try:
                return datetime.fromisoformat(clean_str.replace("Z", "+00:00"))
            except ValueError:
                for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%Y-%m-%d %H:%M:%S"):
                    try:
                        return datetime.strptime(clean_str, fmt)
                    except ValueError:
                        pass
        return None

    @classmethod
    def calculate_performance(cls, po_records: List[Dict[str, Any]]) -> SupplierPerformanceMetrics:
        """
        Calculates empirical performance metrics from a list of historical purchase order dicts.

        Expected keys in each po_record dict:
        - order_date (str or datetime)
        - promised_date (str or datetime, optional)
        - actual_delivery_date (str or datetime, optional)
        - ordered_qty (float, > 0)
        - received_qty (float, >= 0)
        - defective_qty (float, >= 0, optional)
        """
        if not po_records:
            return SupplierPerformanceMetrics(
                on_time_delivery_rate=TrackedValue(
                    value=None, state=ValueState.UNAVAILABLE, source="NO_HISTORICAL_PO_RECORDS"
                ),
                in_full_delivery_rate=TrackedValue(
                    value=None, state=ValueState.UNAVAILABLE, source="NO_HISTORICAL_PO_RECORDS"
                ),
                otif_rate=TrackedValue(value=None, state=ValueState.UNAVAILABLE, source="NO_HISTORICAL_PO_RECORDS"),
                fill_rate=TrackedValue(value=None, state=ValueState.UNAVAILABLE, source="NO_HISTORICAL_PO_RECORDS"),
                mean_lead_time_days=TrackedValue(
                    value=None, state=ValueState.UNAVAILABLE, source="NO_HISTORICAL_PO_RECORDS"
                ),
                lead_time_std_days=TrackedValue(
                    value=None, state=ValueState.UNAVAILABLE, source="NO_HISTORICAL_PO_RECORDS"
                ),
                defect_rate=TrackedValue(value=None, state=ValueState.UNAVAILABLE, source="NO_HISTORICAL_PO_RECORDS"),
                total_orders_evaluated=0,
            )

        valid_orders_count = 0
        on_time_count = 0
        in_full_count = 0
        otif_count = 0

        evaluable_otd_orders = 0
        evaluable_in_full_orders = 0
        evaluable_otif_orders = 0

        total_ordered_qty = 0.0
        total_received_qty = 0.0
        total_defective_qty = 0.0
        has_defect_data = False

        lead_times_days: List[float] = []

        for record in po_records:
            order_date = cls._parse_date(record.get("order_date"))
            promised_date = cls._parse_date(record.get("promised_date"))
            actual_date = cls._parse_date(record.get("actual_delivery_date"))

            try:
                ordered_qty = float(record.get("ordered_qty", 0.0))
            except (ValueError, TypeError):
                ordered_qty = 0.0

            try:
                received_qty = float(record.get("received_qty", 0.0))
            except (ValueError, TypeError):
                received_qty = 0.0

            if record.get("defective_qty") is not None:
                try:
                    defective_qty = float(record["defective_qty"])
                    total_defective_qty += max(0.0, defective_qty)
                    has_defect_data = True
                except (ValueError, TypeError):
                    pass

            if ordered_qty <= 0.0:
                continue

            valid_orders_count += 1
            total_ordered_qty += ordered_qty
            total_received_qty += max(0.0, received_qty)

            # Lead time calculation
            if order_date and actual_date and actual_date >= order_date:
                lt_days = (actual_date - order_date).total_seconds() / 86400.0
                lead_times_days.append(lt_days)

            # On-Time evaluation
            is_on_time: Optional[bool] = None
            if promised_date and actual_date:
                evaluable_otd_orders += 1
                is_on_time = actual_date <= promised_date
                if is_on_time:
                    on_time_count += 1

            # In-Full evaluation
            is_in_full: Optional[bool] = None
            if received_qty >= 0.0:
                evaluable_in_full_orders += 1
                is_in_full = received_qty >= ordered_qty
                if is_in_full:
                    in_full_count += 1

            # OTIF evaluation
            if is_on_time is not None and is_in_full is not None:
                evaluable_otif_orders += 1
                if is_on_time and is_in_full:
                    otif_count += 1

        if valid_orders_count == 0:
            return SupplierPerformanceMetrics(
                on_time_delivery_rate=TrackedValue(
                    value=None, state=ValueState.UNAVAILABLE, source="NO_VALID_PO_RECORDS"
                ),
                in_full_delivery_rate=TrackedValue(
                    value=None, state=ValueState.UNAVAILABLE, source="NO_VALID_PO_RECORDS"
                ),
                otif_rate=TrackedValue(value=None, state=ValueState.UNAVAILABLE, source="NO_VALID_PO_RECORDS"),
                fill_rate=TrackedValue(value=None, state=ValueState.UNAVAILABLE, source="NO_VALID_PO_RECORDS"),
                mean_lead_time_days=TrackedValue(
                    value=None, state=ValueState.UNAVAILABLE, source="NO_VALID_PO_RECORDS"
                ),
                lead_time_std_days=TrackedValue(value=None, state=ValueState.UNAVAILABLE, source="NO_VALID_PO_RECORDS"),
                defect_rate=TrackedValue(value=None, state=ValueState.UNAVAILABLE, source="NO_VALID_PO_RECORDS"),
                total_orders_evaluated=0,
            )

        otd_val = round(on_time_count / evaluable_otd_orders, 4) if evaluable_otd_orders > 0 else None
        in_full_val = round(in_full_count / evaluable_in_full_orders, 4) if evaluable_in_full_orders > 0 else None
        otif_val = round(otif_count / evaluable_otif_orders, 4) if evaluable_otif_orders > 0 else None

        fill_rate_val = round(min(1.0, total_received_qty / total_ordered_qty), 4) if total_ordered_qty > 0 else None

        if lead_times_days:
            mean_lt = float(sum(lead_times_days) / len(lead_times_days))
            if len(lead_times_days) > 1:
                variance_lt = sum((x - mean_lt) ** 2 for x in lead_times_days) / (len(lead_times_days) - 1)
                std_lt = math.sqrt(max(0.0, variance_lt))
            else:
                std_lt = 0.0
            mean_lt_val: Optional[float] = round(mean_lt, 2)
            std_lt_val: Optional[float] = round(std_lt, 2)
        else:
            mean_lt_val = None
            std_lt_val = None

        if has_defect_data and total_received_qty > 0.0:
            defect_val: Optional[float] = round(total_defective_qty / total_received_qty, 4)
        else:
            defect_val = None

        return SupplierPerformanceMetrics(
            on_time_delivery_rate=TrackedValue(
                value=otd_val,
                state=ValueState.DERIVED if otd_val is not None else ValueState.UNAVAILABLE,
                source="HISTORICAL_PO_ON_TIME_COUNT",
            ),
            in_full_delivery_rate=TrackedValue(
                value=in_full_val,
                state=ValueState.DERIVED if in_full_val is not None else ValueState.UNAVAILABLE,
                source="HISTORICAL_PO_IN_FULL_COUNT",
            ),
            otif_rate=TrackedValue(
                value=otif_val,
                state=ValueState.DERIVED if otif_val is not None else ValueState.UNAVAILABLE,
                source="HISTORICAL_PO_OTIF_COUNT",
            ),
            fill_rate=TrackedValue(
                value=fill_rate_val,
                state=ValueState.DERIVED if fill_rate_val is not None else ValueState.UNAVAILABLE,
                source="HISTORICAL_PO_TOTAL_QTY_RATIO",
            ),
            mean_lead_time_days=TrackedValue(
                value=mean_lt_val,
                state=ValueState.DERIVED if mean_lt_val is not None else ValueState.UNAVAILABLE,
                source="HISTORICAL_PO_DELIVERY_INTERVALS",
            ),
            lead_time_std_days=TrackedValue(
                value=std_lt_val,
                state=ValueState.DERIVED if std_lt_val is not None else ValueState.UNAVAILABLE,
                source="HISTORICAL_PO_DELIVERY_STD",
            ),
            defect_rate=TrackedValue(
                value=defect_val,
                state=ValueState.DERIVED if defect_val is not None else ValueState.UNAVAILABLE,
                source="HISTORICAL_DEFECT_QTY_RATIO",
            ),
            total_orders_evaluated=valid_orders_count,
        )
