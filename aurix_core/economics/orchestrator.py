"""Master Orchestrator for Phase 8 Financial Intelligence & Scenario Simulation."""

import datetime
import uuid
from typing import Any, Dict, List, Optional
from aurix_core.economics.config import EconomicsConfiguration
from aurix_core.economics.financials import FinancialEngine
from aurix_core.economics.simulator import ScenarioEngine
from aurix_core.schema.phase5_contract import MissingInput, TrackedValue
from aurix_core.schema.phase9_contract import Phase9InputContract
from aurix_core.schema.phase10_contract import (
    Phase10InputContract,
    ScenarioOverride,
    ScenarioResult,
    ScenarioType,
    TCOBreakdown,
    WorkingCapitalExposure,
)

__all__ = ["Phase8Orchestrator"]


class Phase8Orchestrator:
    """Master Orchestrator for Phase 8 Financial Intelligence & Scenario Simulation."""

    def __init__(
        self,
        phase7b_decision_output: Optional[Dict[str, Any]] = None,
        custom_scenarios: Optional[List[Dict[str, Any]]] = None,
        config_override: Optional[Any] = None,
    ) -> None:
        self.phase7b_data = phase7b_decision_output or {}
        self.custom_scenarios = custom_scenarios or []

        if isinstance(config_override, EconomicsConfiguration):
            self.config = config_override
        elif isinstance(config_override, dict):
            self.config = EconomicsConfiguration(config_override)
        else:
            self.config = EconomicsConfiguration()

        self.run_id = str(uuid.uuid4())
        self.timestamp = datetime.datetime.now().isoformat()

    def execute(self) -> Dict[str, Any]:
        """Executes the complete Phase 8 financial intelligence pipeline and returns dictionary output."""
        contract = self.process_economics()
        return contract.model_dump()

    def process_economics(self) -> Phase10InputContract:
        """Consumes Phase 7B decision contracts and computes financial intelligence and scenarios."""
        missing_inputs: List[MissingInput] = []
        limitations: List[str] = []

        # 1. Parse Phase 7B Decision Contract
        if not self.phase7b_data:
            missing_inputs.append(
                MissingInput(
                    field="phase7b_decision_output",
                    state="USER_INPUT_REQUIRED",
                    domain="economics",
                    severity="CRITICAL",
                    prompt="No Phase 7B decision engine output provided.",
                )
            )
            return Phase10InputContract(
                status="USER_INPUT_REQUIRED",
                missing_inputs=missing_inputs,
                portfolio_financials_by_currency={},
                sku_working_capital={},
                sku_tco={},
                scenarios={},
                limitations=["MISSING_PHASE7B_DECISION_INPUTS"],
                provenance={
                    "phase8_run_id": self.run_id,
                    "timestamp": self.timestamp,
                    "engine_version": "8.0.0-economics",
                },
            )

        p9_contract = Phase9InputContract(**self.phase7b_data)
        decisions = p9_contract.decisions

        all_exposures: List[WorkingCapitalExposure] = []
        sku_working_capital_map: Dict[str, List[WorkingCapitalExposure]] = {}
        sku_tco_map: Dict[str, TCOBreakdown] = {}

        # 2. Compute Working Capital & TCO per SKU/Decision
        for sku_id, opt_result in decisions.items():
            if opt_result.status.value != "RECOMMENDED" or not opt_result.recommended_action:
                continue

            rec = opt_result.recommended_action
            node_id = rec.destination_node
            curr = rec.financial_impact.currency

            inv_val_tv = rec.optimized_state.inventory_value
            inv_units = (
                float(inv_val_tv.value) / 10.0
                if inv_val_tv and inv_val_tv.value is not None
                else None
            )
            unit_cost = 10.0 if inv_units and inv_units > 0 else None

            wc_exp = FinancialEngine.calculate_working_capital(
                sku_id=sku_id,
                node_id=node_id,
                on_hand_units=inv_units,
                cycle_stock_units=inv_units * 0.5 if inv_units else None,
                safety_stock_units=inv_units * 0.5 if inv_units else None,
                excess_units=0.0,
                unit_cost=unit_cost,
                currency=curr,
                config=self.config,
            )

            all_exposures.append(wc_exp)
            if sku_id not in sku_working_capital_map:
                sku_working_capital_map[sku_id] = []
            sku_working_capital_map[sku_id].append(wc_exp)

            # TCO calculation
            purchase_tv = TrackedValue(
                value=wc_exp.total_inventory_value.value,
                state=wc_exp.total_inventory_value.state,
                source="PURCHASE_ESTIMATE",
            )
            tco = FinancialEngine.calculate_tco(
                purchase_cost=purchase_tv,
                freight_cost=rec.financial_impact.total_cost_change,
                holding_cost=wc_exp.annual_holding_cost,
                currency=curr,
            )
            sku_tco_map[sku_id] = tco

        # 3. Portfolio Aggregation by Currency
        portfolio_financials = FinancialEngine.aggregate_portfolio_by_currency(all_exposures)

        # 4. Standard Scenario Simulation Execution
        scenarios_result: Dict[str, ScenarioResult] = {}
        base_inv_by_curr: Dict[str, float] = {}
        base_hold_by_curr: Dict[str, float] = {}
        base_tco_by_curr: Dict[str, float] = {}

        for curr, port in portfolio_financials.items():
            if port.total_inventory_value.value is not None:
                base_inv_by_curr[curr] = float(port.total_inventory_value.value)
            if port.total_holding_cost.value is not None:
                base_hold_by_curr[curr] = float(port.total_holding_cost.value)

        total_tco_val = sum(
            (
                float(tco.total_cost_of_ownership.value)
                for tco in sku_tco_map.values()
                if tco.total_cost_of_ownership and tco.total_cost_of_ownership.value is not None
            ),
            0.0,
        )
        if total_tco_val > 0.0 and base_inv_by_curr:
            first_curr = list(base_inv_by_curr.keys())[0]
            base_tco_by_curr[first_curr] = total_tco_val

        # Execute Default Standard Scenarios
        default_scenarios = [
            (
                "SCEN-DEMAND-UP",
                ScenarioType.DEMAND_SHOCK,
                "Simulates a +10% demand surge impact on inventory and holding costs.",
                ScenarioOverride(demand_multiplier=1.10),
            ),
            (
                "SCEN-FREIGHT-UP",
                ScenarioType.FREIGHT_COST_ESCALATION,
                "Simulates a +15% freight cost escalation on total cost of ownership.",
                ScenarioOverride(freight_cost_multiplier=1.15),
            ),
        ]

        for sc_id, sc_type, desc, overrides in default_scenarios:
            scen_res = ScenarioEngine.simulate_scenario(
                scenario_id=sc_id,
                scenario_type=sc_type,
                description=desc,
                overrides=overrides,
                baseline_inventory_value_by_currency=base_inv_by_curr,
                baseline_holding_cost_by_currency=base_hold_by_curr,
                baseline_tco_by_currency=base_tco_by_curr,
                config=self.config,
            )
            scenarios_result[sc_id] = scen_res

        # Execute Custom Scenarios if provided
        for idx, custom in enumerate(self.custom_scenarios):
            sc_id = custom.get("scenario_id", f"SCEN-CUSTOM-{idx + 1}")
            try:
                sc_type = ScenarioType[custom.get("scenario_type", "DEMAND_SHOCK")]
            except KeyError:
                sc_type = ScenarioType.DEMAND_SHOCK

            desc = custom.get("description", "Custom user-defined scenario simulation.")
            overrides = ScenarioOverride(**custom.get("overrides", {}))

            scen_res = ScenarioEngine.simulate_scenario(
                scenario_id=sc_id,
                scenario_type=sc_type,
                description=desc,
                overrides=overrides,
                baseline_inventory_value_by_currency=base_inv_by_curr,
                baseline_holding_cost_by_currency=base_hold_by_curr,
                baseline_tco_by_currency=base_tco_by_curr,
                config=self.config,
            )
            scenarios_result[sc_id] = scen_res

        overall_status = "COMPUTABLE" if all_exposures else "NO_FINANCIAL_EXPOSURES_FOUND"

        return Phase10InputContract(
            status=overall_status,
            missing_inputs=missing_inputs,
            portfolio_financials_by_currency=portfolio_financials,
            sku_working_capital=sku_working_capital_map,
            sku_tco=sku_tco_map,
            scenarios=scenarios_result,
            limitations=limitations,
            provenance={
                "phase8_run_id": self.run_id,
                "phase7b_run_id": p9_contract.provenance.get("phase7b_run_id", "UNKNOWN"),
                "timestamp": self.timestamp,
                "engine_version": "8.0.0-economics",
            },
        )