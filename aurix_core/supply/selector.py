"""Supplier selection engine implementing refined deterministic ranking hierarchy."""

from typing import List, Optional, Tuple
from aurix_core.schema.phase6_contract import (
    CapacityStatus,
    SupplierEvaluation,
    SupplyRiskLevel,
    SupplyRiskSummary,
)


class SupplierSelector:
    """Ranks evaluated supplier candidates and selects the optimal primary supplier deterministically."""

    @staticmethod
    def _risk_level_rank_key(level: SupplyRiskLevel) -> int:
        """
        Helper to rank supply risk level preference:
        LOW (0) > MODERATE (1) > HIGH (2) > CRITICAL (3) > NOT_ASSESSABLE (4).
        """
        mapping = {
            SupplyRiskLevel.LOW: 0,
            SupplyRiskLevel.MODERATE: 1,
            SupplyRiskLevel.HIGH: 2,
            SupplyRiskLevel.CRITICAL: 3,
            SupplyRiskLevel.NOT_ASSESSABLE: 4,
        }
        return mapping.get(level, 4)

    @staticmethod
    def _capacity_rank_key(status: CapacityStatus) -> int:
        """Helper to rank capacity status preference: SUFFICIENT (0) > UNKNOWN (1) > CONSTRAINED (2)."""
        if status == CapacityStatus.CAPACITY_SUFFICIENT:
            return 0
        if status == CapacityStatus.CAPACITY_UNKNOWN:
            return 1
        return 2

    @classmethod
    def select_supplier(
        cls, evaluations: List[SupplierEvaluation]
    ) -> Tuple[Optional[SupplierEvaluation], List[SupplierEvaluation], SupplyRiskSummary]:
        """
        Ranks candidate evaluations deterministically and selects the primary recommended supplier.

        Refined Deterministic Sorting Hierarchy:
        1. Eligibility (Eligible candidates first)
        2. Supply Risk Level (LOW > MODERATE > HIGH > CRITICAL > NOT_ASSESSABLE)
        3. Capacity Status (SUFFICIENT > UNKNOWN > CONSTRAINED)
        4. Supply Risk Score (Lower numerical risk score first)
        5. Total Purchase Cost (Lower cost first)
        6. Supplier ID (Alphabetical tie-breaker for 100% deterministic reproducibility)
        """
        if not evaluations:
            risk_summary = SupplyRiskSummary(
                overall_risk_level=SupplyRiskLevel.CRITICAL,
                single_source_dependency=False,
                primary_risk_drivers=["NO_CANDIDATE_SUPPLIERS_AVAILABLE"],
            )
            return None, [], risk_summary

        def sort_key(eval_item: SupplierEvaluation) -> Tuple[bool, int, int, float, float, str]:
            cost = eval_item.total_purchase_cost if eval_item.total_purchase_cost is not None else 1e12
            return (
                not eval_item.is_eligible,
                cls._risk_level_rank_key(eval_item.supply_risk_level),
                cls._capacity_rank_key(eval_item.capacity_status),
                eval_item.supply_risk_score,
                cost,
                eval_item.supplier_id,
            )

        sorted_evals = sorted(evaluations, key=sort_key)
        eligible_evals = [e for e in sorted_evals if e.is_eligible]

        ranked_evaluations: List[SupplierEvaluation] = []
        recommended_supplier: Optional[SupplierEvaluation] = None

        rank_counter = 1
        for eval_item in sorted_evals:
            item_copy = eval_item.model_copy()
            if not item_copy.is_eligible:
                item_copy.selection_status = "REJECTED"
                item_copy.rank = None
            elif rank_counter == 1:
                item_copy.selection_status = "RECOMMENDED"
                item_copy.rank = 1
                recommended_supplier = item_copy
                rank_counter += 1
            else:
                item_copy.selection_status = "ALTERNATIVE"
                item_copy.rank = rank_counter
                rank_counter += 1

            ranked_evaluations.append(item_copy)

        # Build Supply Risk Summary
        single_source = len(eligible_evals) == 1
        risk_drivers: List[str] = []

        if not eligible_evals:
            overall_risk = SupplyRiskLevel.CRITICAL
            risk_drivers.append("NO_ELIGIBLE_SUPPLIERS")
        else:
            primary = recommended_supplier or eligible_evals[0]
            overall_risk = primary.supply_risk_level

            if single_source:
                risk_drivers.append("SINGLE_SOURCE_DEPENDENCY")

            if primary.capacity_status == CapacityStatus.CAPACITY_CONSTRAINED:
                risk_drivers.append("PRIMARY_SUPPLIER_CAPACITY_CONSTRAINED")

            if primary.supply_risk_level in (SupplyRiskLevel.HIGH, SupplyRiskLevel.CRITICAL):
                risk_drivers.append(f"PRIMARY_SUPPLIER_RISK_{primary.supply_risk_level.value}")

            if primary.moq_applied:
                risk_drivers.append("PRIMARY_SUPPLIER_MOQ_EXCEEDS_REQUIREMENT")

        if not risk_drivers:
            risk_drivers.append("LOW_SUPPLY_CHAIN_FRICTION")

        supply_risk_summary = SupplyRiskSummary(
            overall_risk_level=overall_risk,
            single_source_dependency=single_source,
            primary_risk_drivers=risk_drivers,
        )

        return recommended_supplier, ranked_evaluations, supply_risk_summary
