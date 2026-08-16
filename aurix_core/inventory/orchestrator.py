import datetime
import uuid
from typing import Any, Dict, Optional
from aurix_core.inventory.config import InventoryConfiguration
from aurix_core.inventory.gate import InventoryReadinessGate
from aurix_core.inventory.mathematics import InventoryMathematics
from aurix_core.inventory.policy import InventoryPolicyEngine
from aurix_core.inventory.risk import InventoryRiskEvaluator
from aurix_core.schema.phase4_contract import Phase4InputContract
from aurix_core.schema.phase5_contract import (
    FinancialExposure,
    InventoryMetrics,
    MissingInput,
    Phase5InputContract,
    TrackedValue,
    ValueState,
)


class Phase4Orchestrator:
    """Master Orchestrator for Phase 4 Inventory Intelligence."""

    def __init__(
        self,
        phase3_portfolio_output: Dict[str, Any],
        user_inputs: Optional[Dict[str, Dict[str, Any]]] = None,
        config_override: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.phase3_data = phase3_portfolio_output
        self.user_inputs = user_inputs or {}
        self.config = config_override or {}
        self.run_id = str(uuid.uuid4())
        self.timestamp = datetime.datetime.now().isoformat()

    def process_sku(self, sku_id: str, phase3_sku_contract: Dict[str, Any]) -> Phase5InputContract:
        p3_contract = Phase4InputContract(**phase3_sku_contract)
        sku_user_data = self.user_inputs.get(sku_id, {})

        forecast_points = p3_contract.forecast
        if forecast_points:
            daily_demand = float(sum(p.point_forecast for p in forecast_points) / len(forecast_points))
            demand_source = "PHASE_3_FORECAST"
        else:
            daily_demand = float(sku_user_data.get("expected_daily_demand", 0.0))
            demand_source = "USER_PROVIDED" if daily_demand > 0.0 else "UNAVAILABLE"

        best_eval = [
            m for m in p3_contract.model_competition if m.model_id == p3_contract.champion_model and m.rmse is not None
        ]
        if best_eval and best_eval[0].rmse is not None:
            demand_std = float(best_eval[0].rmse)
            uncertainty_source = "PHASE_3_MODEL_RMSE"
        else:
            demand_std = float(sku_user_data.get("demand_std", daily_demand * 0.20))
            uncertainty_source = "USER_PROVIDED_OR_ESTIMATED"

        lead_time_days = sku_user_data.get("lead_time_days")
        lead_time_source = "USER_PROVIDED" if lead_time_days is not None else "UNAVAILABLE"

        gate_payload = {
            "lead_time_days": lead_time_days,
            "expected_daily_demand": daily_demand if daily_demand > 0.0 else None,
            "unit_cost": sku_user_data.get("unit_cost"),
        }
        is_computable, missing_raw = InventoryReadinessGate.evaluate(gate_payload)
        missing_inputs = [MissingInput(**m) for m in missing_raw]

        if not is_computable or lead_time_days is None or daily_demand <= 0.0:
            return Phase5InputContract(
                sku_id=sku_id,
                status="USER_INPUT_REQUIRED",
                missing_inputs=missing_inputs,
                metrics=None,
                risk_status="NOT_ASSESSABLE",
                financials=None,
                policy_applied=None,
                limitations=p3_contract.limitations + ["CRITICAL_INVENTORY_INPUTS_MISSING"],
                provenance={
                    "phase4_run_id": self.run_id,
                    "phase3_run_id": p3_contract.provenance.get("phase3_run_id", "UNKNOWN"),
                    "dataset_hash": p3_contract.provenance.get("dataset_hash", "UNKNOWN"),
                    "engine_version": "4.0.0",
                },
            )

        srv_level_val = sku_user_data.get("service_level", InventoryConfiguration.DEFAULT_SERVICE_LEVEL)
        srv_source = "USER_PROVIDED" if "service_level" in sku_user_data else "CONFIGURATION"
        z_score = InventoryConfiguration.get_z_score(float(srv_level_val))

        lead_time_std = float(sku_user_data.get("lead_time_std", 0.0))
        combined_std = InventoryMathematics.calculate_combined_std(
            daily_demand_mean=daily_demand,
            daily_demand_std=demand_std,
            lead_time_days=float(lead_time_days),
            lead_time_std=lead_time_std,
        )
        safety_stock_val = InventoryMathematics.calculate_safety_stock(z_score, combined_std)
        reorder_point_val = InventoryMathematics.calculate_reorder_point(
            daily_demand, float(lead_time_days), safety_stock_val
        )

        unit_cost = sku_user_data.get("unit_cost")
        ordering_cost = sku_user_data.get("ordering_cost", 50.0)
        holding_rate = sku_user_data.get("holding_cost_rate", InventoryConfiguration.DEFAULT_HOLDING_COST_RATE)

        if unit_cost is not None and unit_cost > 0.0:
            annual_demand = daily_demand * InventoryConfiguration.DEFAULT_DAYS_IN_YEAR
            holding_cost_unit_year = float(unit_cost) * float(holding_rate)
            eoq_val = InventoryMathematics.calculate_eoq(annual_demand, float(ordering_cost), holding_cost_unit_year)
            eoq_state = ValueState.DERIVED
        else:
            eoq_val = None
            eoq_state = ValueState.UNAVAILABLE

        on_hand = float(sku_user_data.get("on_hand_qty", 0.0))
        inbound = float(sku_user_data.get("inbound_qty", 0.0))
        committed = float(sku_user_data.get("committed_qty", 0.0))

        inv_position = InventoryMathematics.calculate_inventory_position(on_hand, inbound, committed)
        coverage_days = InventoryMathematics.calculate_coverage_days(on_hand, daily_demand)

        moq = sku_user_data.get("moq")
        pack_size = sku_user_data.get("pack_size")
        policy_res = InventoryPolicyEngine.evaluate_policy(
            inventory_position=inv_position,
            reorder_point=reorder_point_val,
            eoq=eoq_val,
            daily_demand=daily_demand,
            lead_time_days=float(lead_time_days),
            moq=float(moq) if moq else None,
            pack_size=float(pack_size) if pack_size else None,
        )

        risk_res = InventoryRiskEvaluator.evaluate_risk(
            on_hand_qty=on_hand,
            inventory_position=inv_position,
            reorder_point=reorder_point_val,
            safety_stock=safety_stock_val,
            lead_time_days=float(lead_time_days),
            daily_demand=daily_demand,
        )

        if unit_cost is not None and unit_cost > 0.0:
            inv_value = round(on_hand * float(unit_cost), 2)
            annual_holding = round(inv_value * float(holding_rate), 2)
            fin_exposure = FinancialExposure(
                inventory_value=TrackedValue(value=inv_value, state=ValueState.DERIVED, source="UNIT_COST_X_ON_HAND"),
                holding_cost_exposure=TrackedValue(
                    value=annual_holding, state=ValueState.DERIVED, source="ANNUAL_HOLDING_RATE"
                ),
                stockout_cost_exposure=TrackedValue(
                    value=None, state=ValueState.UNAVAILABLE, source="NO_STOCKOUT_COST_PROVIDED"
                ),
            )
        else:
            fin_exposure = FinancialExposure(
                inventory_value=TrackedValue(value=None, state=ValueState.UNAVAILABLE, source="NO_UNIT_COST"),
                holding_cost_exposure=TrackedValue(value=None, state=ValueState.UNAVAILABLE, source="NO_UNIT_COST"),
                stockout_cost_exposure=TrackedValue(
                    value=None, state=ValueState.UNAVAILABLE, source="NO_STOCKOUT_COST"
                ),
            )

        metrics = InventoryMetrics(
            safety_stock=TrackedValue(
                value=safety_stock_val,
                state=ValueState.DERIVED,
                source="COMBINED_DEMAND_LEAD_TIME_STD",
            ),
            reorder_point=TrackedValue(
                value=reorder_point_val,
                state=ValueState.DERIVED,
                source="DEMAND_LEAD_TIME_PLUS_SAFETY_STOCK",
            ),
            economic_order_quantity=TrackedValue(
                value=eoq_val,
                state=eoq_state,
                source="CLASSIC_EOQ_FORMULA" if eoq_val else "UNAVAILABLE",
            ),
            order_quantity=TrackedValue(
                value=policy_res["constrained_order_quantity"],
                state=ValueState.DERIVED,
                source=policy_res["policy"],
                notes=policy_res["constraint_reason"],
            ),
            inventory_position=TrackedValue(
                value=inv_position,
                state=ValueState.DERIVED,
                source="ON_HAND_PLUS_INBOUND_MINUS_COMMITTED",
            ),
            inventory_coverage_days=TrackedValue(
                value=coverage_days,
                state=ValueState.DERIVED if coverage_days else ValueState.UNAVAILABLE,
                source="ON_HAND_DIVIDED_BY_DAILY_DEMAND",
            ),
        )

        return Phase5InputContract(
            sku_id=sku_id,
            status="COMPUTABLE",
            missing_inputs=missing_inputs,
            metrics=metrics,
            risk_status=risk_res["stockout_risk"],
            financials=fin_exposure,
            policy_applied=policy_res["policy"],
            limitations=p3_contract.limitations,
            provenance={
                "phase4_run_id": self.run_id,
                "phase3_run_id": p3_contract.provenance.get("phase3_run_id", "UNKNOWN"),
                "dataset_hash": p3_contract.provenance.get("dataset_hash", "UNKNOWN"),
                "demand_source": demand_source,
                "demand_uncertainty_source": uncertainty_source,
                "lead_time_source": lead_time_source,
                "service_level_source": srv_source,
                "engine_version": "4.0.0",
            },
        )

    def execute(self) -> Dict[str, Any]:
        sku_forecasts = self.phase3_data.get("sku_forecasts", {})
        portfolio_results: Dict[str, Any] = {}

        total_skus = len(sku_forecasts)
        computable_count = 0
        input_required_count = 0
        total_safety_stock = 0.0
        total_inventory_value = 0.0
        risk_dist: Dict[str, int] = {}

        for sku, p3_dict in sku_forecasts.items():
            contract_res = self.process_sku(sku, p3_dict)
            portfolio_results[sku] = contract_res.model_dump()

            if contract_res.status == "COMPUTABLE":
                computable_count += 1
                if contract_res.metrics and contract_res.metrics.safety_stock:
                    ss_val = contract_res.metrics.safety_stock.value
                    if ss_val:
                        total_safety_stock += ss_val
                if contract_res.financials and contract_res.financials.inventory_value:
                    val = contract_res.financials.inventory_value.value
                    if val:
                        total_inventory_value += val
            else:
                input_required_count += 1

            r_status = contract_res.risk_status or "UNKNOWN"
            risk_dist[r_status] = risk_dist.get(r_status, 0) + 1

        summary = {
            "total_skus": total_skus,
            "computable_skus": computable_count,
            "input_required_skus": input_required_count,
            "total_safety_stock_units": round(total_safety_stock, 2),
            "total_inventory_value": round(total_inventory_value, 2),
            "risk_distribution": risk_dist,
        }

        return {
            "run_id": self.run_id,
            "timestamp": self.timestamp,
            "portfolio_summary": summary,
            "sku_inventory_intelligence": portfolio_results,
            "phase5_contract_status": "READY",
        }
