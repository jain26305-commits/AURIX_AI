"""Deterministic supplier selection, ranking, and single-source dependency detection engine."""

from typing import Any, Dict, List, Optional, Tuple
from aurix_core.schema.phase6_contract import CapacityStatus, SupplyRiskLevel


class SupplierSelectorSummary:
    """Summary of portfolio-wide or requirement-specific supplier selection state."""

    def __init__(
        self,
        single_source_dependency: bool = False,
        overall_risk_level: SupplyRiskLevel = SupplyRiskLevel.LOW,
        primary_risk_drivers: Optional[List[str]] = None,
    ) -> None:
        self.single_source_dependency = single_source_dependency
        self.overall_risk_level = overall_risk_level
        self.primary_risk_drivers = primary_risk_drivers or []


class SupplierSelector:
    """
    Deterministic supplier selection engine.
    Ranks eligible suppliers based on risk score, capacity, total cost, and lead-time stability,
    enforcing stable tie-breaking and single-source dependency detection.
    """

    @staticmethod
    def select_best(candidates: List[Dict[str, Any]], required_qty: float) -> Dict[str, Any]:
        """Legacy helper for dict-based candidate evaluation and selection."""
        if not candidates:
            return {"selected_supplier_id": None, "single_source_dependency": True}

        # Simple deterministic evaluation on raw dicts
        valid_candidates = [c for c in candidates if c.get("unit_price", 0.0) > 0.0]
        if not valid_candidates:
            return {"selected_supplier_id": None, "single_source_dependency": True}

        # Sort deterministically by risk_score asc, unit_price asc, supplier_id asc
        sorted_candidates = sorted(
            valid_candidates,
            key=lambda x: (
                x.get("risk_score", 0.0),
                x.get("unit_price", 0.0),
                str(x.get("supplier_id", ""))
            )
        )
        selected = sorted_candidates[0]
        single_source = len(valid_candidates) == 1

        return {
            "selected_supplier_id": selected.get("supplier_id"),
            "single_source_dependency": single_source,
            "ranked_candidates": sorted_candidates,
        }

    @staticmethod
    def select_supplier(
        evaluations: List[Any],
    ) -> Tuple[Optional[Any], List[Any], SupplierSelectorSummary]:
        """
        Deterministically selects the optimal supplier from a list of evaluated candidates.

        Selection Criteria Hierarchy:
        1. Eligibility (Must be eligible).
        2. Supply Risk Level & Score (Lower risk level and score are preferred).
        3. Capacity Status / Sufficiency.
        4. Total Purchase Cost (Lower cost is preferred).
        5. Lead Time Reliability / Standard Deviation.
        6. Stable Tie-Breaker (Alphabetical supplier_id).
        """
        eligible = [e for e in evaluations if getattr(e, "is_eligible", False)]

        if not eligible:
            summary = SupplierSelectorSummary(
                single_source_dependency=len(evaluations) <= 1,
                overall_risk_level=SupplyRiskLevel.CRITICAL,
                primary_risk_drivers=["NO_ELIGIBLE_SUPPLIERS"],
            )
            return None, [], summary

        # Deterministic sorting key
        def _sort_key(eval_res: Any) -> Tuple[Any, ...]:
            # 1. Risk Level Rank (LOW=1, MODERATE=2, HIGH=3, CRITICAL=4)
            risk_level = getattr(eval_res, "supply_risk_level", None)
            risk_level_str = ""
            if risk_level is not None:
                val_attr = getattr(risk_level, "value", risk_level)
                risk_level_str = str(val_attr).upper()

            level_map = {
                "LOW": 1,
                "LOW_RISK": 1,
                "MODERATE": 2,
                "MODERATE_RISK": 2,
                "HIGH": 3,
                "HIGH_RISK": 3,
                "CRITICAL": 4,
                "CRITICAL_RISK": 4,
            }
            level_rank = level_map.get(risk_level_str, 2)

            # 2. Risk Score
            risk_score = getattr(eval_res, "supply_risk_score", None)
            if risk_score is None:
                risk_score = 0.5

            # 3. Capacity Status Penalty Rank (Sufficient = 0, Unknown = 1, Constrained = 2)
            cap_status = getattr(eval_res, "capacity_status", None)
            cap_rank = 0
            if cap_status == CapacityStatus.CAPACITY_CONSTRAINED:
                cap_rank = 2
            elif cap_status == CapacityStatus.CAPACITY_UNKNOWN:
                cap_rank = 1

            # 4. Total Cost
            cost = getattr(eval_res, "total_purchase_cost", None)
            if cost is None:
                cost = float("inf")

            # 5. Lead Time Standard Deviation
            lt_std = 0.0
            lt_std_days = getattr(eval_res, "lead_time_std_days", None)
            if lt_std_days is not None:
                val = getattr(lt_std_days, "value", None)
                if val is not None:
                    try:
                        lt_std = float(val)
                    except (ValueError, TypeError):
                        lt_std = 0.0

            # 6. Tie Breaker: Supplier ID
            supplier_id = getattr(eval_res, "supplier_id", "")
            if supplier_id is None:
                supplier_id = ""

            return (
                level_rank,
                risk_score,
                cap_rank,
                cost,
                lt_std,
                supplier_id,
            )

        ranked = sorted(eligible, key=_sort_key)
        best_supplier = ranked[0]

        # Update selection status to RECOMMENDED for the top candidate
        if hasattr(best_supplier, "model_copy"):
            best_supplier = best_supplier.model_copy(update={"selection_status": "RECOMMENDED"})
            ranked[0] = best_supplier
        else:
            try:
                setattr(best_supplier, "selection_status", "RECOMMENDED")
            except Exception:
                pass

        single_source = len(eligible) == 1
        risk_drivers = []
        if single_source:
            risk_drivers.append("SINGLE_SOURCE_DEPENDENCY")

        summary = SupplierSelectorSummary(
            single_source_dependency=single_source,
            overall_risk_level=getattr(best_supplier, "supply_risk_level", SupplyRiskLevel.LOW),
            primary_risk_drivers=risk_drivers,
        )

        return best_supplier, ranked, summary