"""Master Orchestrator for Phase 5 Supply Intelligence & Replenishment Planning."""

import datetime
import uuid
from typing import Any, Dict, List, Optional
from aurix_core.schema.phase5_contract import MissingInput, Phase5InputContract, TrackedValue, ValueState
from aurix_core.schema.phase6_contract import (
    Phase6InputContract,
    ReplenishmentRequirement,
    ReplenishmentUrgency,
    SupplierCandidate,
    SupplierEvaluation,
    SupplyRiskLevel,
    SupplyRiskSummary,
)
from aurix_core.supply.config import SupplyConfiguration
from aurix_core.supply.evaluator import SupplierEvaluator
from aurix_core.supply.performance import SupplierPerformanceCalculator
from aurix_core.supply.selector import SupplierSelector

__all__ = ["Phase5Orchestrator"]


class Phase5Orchestrator:
    """Master Orchestrator for Phase 5 Supply Intelligence & Replenishment Planning."""

    def __init__(
        self,
        phase4_portfolio_output: Dict[str, Any],
        supplier_data: Optional[Dict[str, Any]] = None,
        config_override: Optional[Any] = None,
    ) -> None:
        self.phase4_data = phase4_portfolio_output
        self.supplier_data = supplier_data or {}
        if isinstance(config_override, SupplyConfiguration):
            self.config = config_override
        elif isinstance(config_override, dict):
            self.config = SupplyConfiguration(config_override)
        else:
            self.config = SupplyConfiguration()
        self.run_id = str(uuid.uuid4())
        self.timestamp = datetime.datetime.now().isoformat()

    @staticmethod
    def _to_tracked_value(val: Any, source: str = "SUPPLIER_RECORD") -> Optional[TrackedValue]:
        """Safely wraps raw primitive values or dictionaries into TrackedValue instances."""
        if val is None:
            return None
        if isinstance(val, TrackedValue):
            return val
        if isinstance(val, dict):
            try:
                return TrackedValue(**val)
            except Exception:
                return None
        return TrackedValue(value=val, state=ValueState.OBSERVED, source=source)

    def process_sku(self, sku_id: str, phase4_sku_contract: Dict[str, Any]) -> Phase6InputContract:
        p4_contract = Phase5InputContract(**phase4_sku_contract)

        # 1. Determine Replenishment Requirement from Phase 4 Outputs
        p4_status = p4_contract.status
        order_qty_obj = p4_contract.metrics.order_quantity if p4_contract.metrics else None
        raw_order_qty = float(order_qty_obj.value) if (order_qty_obj and order_qty_obj.value is not None) else 0.0

        risk_status = p4_contract.risk_status or "NOT_ASSESSABLE"
        coverage_days_obj = p4_contract.metrics.inventory_coverage_days if p4_contract.metrics else None
        cov_days = (
            float(coverage_days_obj.value) if (coverage_days_obj and coverage_days_obj.value is not None) else None
        )

        rop_obj = p4_contract.metrics.reorder_point if p4_contract.metrics else None
        rop_val = float(rop_obj.value) if (rop_obj and rop_obj.value is not None) else None

        pos_obj = p4_contract.metrics.inventory_position if p4_contract.metrics else None
        pos_val = float(pos_obj.value) if (pos_obj and pos_obj.value is not None) else None

        # Determine Urgency
        if p4_status != "COMPUTABLE" or raw_order_qty <= 0.0:
            replenishment_required = False
            urgency = ReplenishmentUrgency.NO_ACTION
            replenishment_reason = f"No replenishment required by Phase 4 policy (Status: {p4_status})."
        elif risk_status == "STOCKOUT_IMMINENT":
            replenishment_required = True
            urgency = ReplenishmentUrgency.EXPEDITED_REPLENISHMENT
            replenishment_reason = "Stockout is imminent. Expedited replenishment action required."
        elif risk_status == "HIGH_RISK":
            replenishment_required = True
            urgency = ReplenishmentUrgency.REPLENISH_NOW
            replenishment_reason = "Inventory position at or below ROP. Triggering replenishment now."
        elif risk_status == "MODERATE_RISK":
            replenishment_required = True
            urgency = ReplenishmentUrgency.PLAN_REPLENISHMENT
            replenishment_reason = "Inventory approaching reorder threshold. Plan replenishment order."
        else:
            replenishment_required = True
            urgency = ReplenishmentUrgency.MONITOR
            replenishment_reason = "Routine replenishment recommendation."

        replenishment_req = ReplenishmentRequirement(
            required=replenishment_required,
            base_required_quantity=raw_order_qty,
            urgency=urgency,
            inventory_coverage_days=cov_days,
            reorder_point=rop_val,
            inventory_position=pos_val,
            reason=replenishment_reason,
        )

        # Uncomputable Phase 4 Input Handling
        if p4_status == "USER_INPUT_REQUIRED":
            empty_risk = SupplyRiskSummary(
                overall_risk_level=SupplyRiskLevel.NOT_ASSESSABLE,
                single_source_dependency=False,
                primary_risk_drivers=["UPSTREAM_PHASE4_INPUT_REQUIRED"],
            )
            return Phase6InputContract(
                sku_id=sku_id,
                status="USER_INPUT_REQUIRED",
                missing_inputs=p4_contract.missing_inputs,
                replenishment=replenishment_req,
                recommended_supplier=None,
                candidate_evaluations=[],
                supply_risk=empty_risk,
                limitations=p4_contract.limitations + ["UPSTREAM_INVENTORY_INPUTS_MISSING"],
                provenance={
                    "phase5_run_id": self.run_id,
                    "phase4_run_id": p4_contract.provenance.get("phase4_run_id", "UNKNOWN"),
                    "dataset_hash": p4_contract.provenance.get("dataset_hash", "UNKNOWN"),
                    "engine_version": "5.0.0",
                },
            )

        # 2. Extract Candidate Supplier Data
        sku_suppliers_raw = self.supplier_data.get(sku_id, [])
        if not sku_suppliers_raw and isinstance(self.supplier_data.get("suppliers"), list):
            sku_suppliers_raw = [s for s in self.supplier_data["suppliers"] if s.get("sku_id") == sku_id]

        if not sku_suppliers_raw:
            missing_supplier_input = MissingInput(
                field="supplier_data",
                state="USER_INPUT_REQUIRED",
                domain="supply",
                severity="CRITICAL",
                prompt=f"No candidate suppliers provided for SKU {sku_id}.",
            )
            empty_risk = SupplyRiskSummary(
                overall_risk_level=SupplyRiskLevel.CRITICAL,
                single_source_dependency=False,
                primary_risk_drivers=["NO_CANDIDATE_SUPPLIERS_PROVIDED"],
            )
            return Phase6InputContract(
                sku_id=sku_id,
                status="USER_INPUT_REQUIRED",
                missing_inputs=[missing_supplier_input],
                replenishment=replenishment_req,
                recommended_supplier=None,
                candidate_evaluations=[],
                supply_risk=empty_risk,
                limitations=p4_contract.limitations + ["NO_SUPPLIERS_AVAILABLE"],
                provenance={
                    "phase5_run_id": self.run_id,
                    "phase4_run_id": p4_contract.provenance.get("phase4_run_id", "UNKNOWN"),
                    "dataset_hash": p4_contract.provenance.get("dataset_hash", "UNKNOWN"),
                    "engine_version": "5.0.0",
                },
            )

        # 3. Process Candidate Evaluations
        candidate_evaluations: List[SupplierEvaluation] = []
        for s_dict in sku_suppliers_raw:
            po_records = s_dict.get("po_history", [])
            perf_metrics = SupplierPerformanceCalculator.calculate_performance(po_records)

            candidate_obj = SupplierCandidate(
                supplier_id=str(s_dict.get("supplier_id", "UNKNOWN")),
                supplier_name=str(s_dict.get("supplier_name", "Unknown Supplier")),
                unit_price=self._to_tracked_value(s_dict.get("unit_price")),
                currency=str(s_dict.get("currency", "USD")),
                lead_time_days=self._to_tracked_value(s_dict.get("lead_time_days")),
                lead_time_std_days=self._to_tracked_value(s_dict.get("lead_time_std_days")),
                moq=self._to_tracked_value(s_dict.get("moq")),
                pack_size=self._to_tracked_value(s_dict.get("pack_size")),
                capacity_units=self._to_tracked_value(s_dict.get("capacity_units")),
                performance=perf_metrics,
            )

            evaluation = SupplierEvaluator.evaluate_supplier(
                candidate=candidate_obj,
                required_quantity=raw_order_qty,
                config=self.config,
            )
            candidate_evaluations.append(evaluation)

        # 4. Select Optimal Primary Supplier
        recommended_supplier, ranked_evaluations, risk_summary = SupplierSelector.select_supplier(candidate_evaluations)

        contract_status = (
            "COMPUTABLE" if recommended_supplier and recommended_supplier.is_eligible else "NO_ELIGIBLE_SUPPLIERS"
        )

        return Phase6InputContract(
            sku_id=sku_id,
            status=contract_status,
            missing_inputs=[],
            replenishment=replenishment_req,
            recommended_supplier=recommended_supplier,
            candidate_evaluations=ranked_evaluations,
            supply_risk=risk_summary,
            limitations=p4_contract.limitations,
            provenance={
                "phase5_run_id": self.run_id,
                "phase4_run_id": p4_contract.provenance.get("phase4_run_id", "UNKNOWN"),
                "dataset_hash": p4_contract.provenance.get("dataset_hash", "UNKNOWN"),
                "engine_version": "5.0.0",
            },
        )

    def execute(self) -> Dict[str, Any]:
        sku_inventory = self.phase4_data.get("sku_inventory_intelligence", {})
        portfolio_results: Dict[str, Any] = {}

        total_skus = len(sku_inventory)
        computable_count = 0
        input_required_count = 0
        no_eligible_count = 0
        replenishment_needed_count = 0
        single_source_count = 0

        total_purchase_spend = 0.0
        currency_set = set()
        risk_dist: Dict[str, int] = {}

        for sku, p4_dict in sku_inventory.items():
            contract_res = self.process_sku(sku, p4_dict)
            portfolio_results[sku] = contract_res.model_dump()

            if contract_res.status == "COMPUTABLE":
                computable_count += 1
            elif contract_res.status == "USER_INPUT_REQUIRED":
                input_required_count += 1
            else:
                no_eligible_count += 1

            if contract_res.replenishment.required:
                replenishment_needed_count += 1

            if contract_res.supply_risk.single_source_dependency:
                single_source_count += 1

            rec_sup = contract_res.recommended_supplier
            if rec_sup and rec_sup.total_purchase_cost is not None:
                total_purchase_spend += rec_sup.total_purchase_cost
                currency_set.add(rec_sup.currency)

            r_level = contract_res.supply_risk.overall_risk_level.value
            risk_dist[r_level] = risk_dist.get(r_level, 0) + 1

        summary = {
            "total_skus": total_skus,
            "computable_skus": computable_count,
            "input_required_skus": input_required_count,
            "no_eligible_supplier_skus": no_eligible_count,
            "replenishment_actions_needed": replenishment_needed_count,
            "single_source_skus": single_source_count,
            "total_estimated_purchase_spend": round(total_purchase_spend, 2),
            "currencies_present": list(currency_set),
            "risk_level_distribution": risk_dist,
        }

        return {
            "run_id": self.run_id,
            "timestamp": self.timestamp,
            "portfolio_summary": summary,
            "sku_supply_intelligence": portfolio_results,
            "phase6_contract_status": "READY",
        }
