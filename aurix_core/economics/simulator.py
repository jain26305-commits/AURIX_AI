"""Deterministic Scenario Simulation Engine for Supply Chain Risk & Economics (Phase 8)."""

from typing import Dict, List, Optional
from aurix_core.economics.config import EconomicsConfiguration
from aurix_core.schema.phase5_contract import TrackedValue, ValueState
from aurix_core.schema.phase10_contract import (
    ScenarioFinancialComparison,
    ScenarioOverride,
    ScenarioResult,
    ScenarioStatus,
    ScenarioType,
)


class ScenarioEngine:
    """Executes deterministic scenario simulations without mutating source baseline data."""

    @classmethod
    def simulate_scenario(
        cls,
        scenario_id: str,
        scenario_type: ScenarioType,
        description: str,
        overrides: ScenarioOverride,
        baseline_inventory_value_by_currency: Optional[Dict[str, float]] = None,
        baseline_holding_cost_by_currency: Optional[Dict[str, float]] = None,
        baseline_tco_by_currency: Optional[Dict[str, float]] = None,
        config: Optional[EconomicsConfiguration] = None,
    ) -> ScenarioResult:
        """
        Executes a scenario simulation by applying overrides to baseline metrics per currency.
        Strictly preserves native currency isolation and Zero-Fabrication principles.
        """
        cfg = config or EconomicsConfiguration()
        limitations: List[str] = []

        base_inv_map = baseline_inventory_value_by_currency or {}
        base_hold_map = baseline_holding_cost_by_currency or {}
        base_tco_map = baseline_tco_by_currency or {}

        all_currencies = sorted(
            list(set(base_inv_map.keys()) | set(base_hold_map.keys()) | set(base_tco_map.keys()))
        )

        if not all_currencies:
            limitations.append("No financial baseline data available for scenario simulation.")
            return ScenarioResult(
                scenario_id=scenario_id,
                scenario_type=scenario_type,
                description=description,
                status=ScenarioStatus.UNAVAILABLE_INPUTS,
                overrides=overrides,
                financial_comparison_by_currency={},
                operational_impact={},
                limitations=limitations,
            )

        financial_comparisons: Dict[str, ScenarioFinancialComparison] = {}

        # Determine Effective Multipliers based on Scenario Overrides
        inv_mult = 1.0
        tco_mult = 1.0

        if overrides.demand_multiplier is not None:
            if overrides.demand_multiplier < 0.0:
                limitations.append("Invalid negative demand multiplier provided. Simulation marked infeasible.")
                return ScenarioResult(
                    scenario_id=scenario_id,
                    scenario_type=scenario_type,
                    description=description,
                    status=ScenarioStatus.INFEASIBLE,
                    overrides=overrides,
                    financial_comparison_by_currency={},
                    operational_impact={},
                    limitations=limitations,
                )
            inv_mult *= overrides.demand_multiplier
            tco_mult *= overrides.demand_multiplier

        if overrides.lead_time_multiplier is not None:
            if overrides.lead_time_multiplier < 0.0:
                limitations.append("Invalid negative lead time multiplier provided. Simulation marked infeasible.")
                return ScenarioResult(
                    scenario_id=scenario_id,
                    scenario_type=scenario_type,
                    description=description,
                    status=ScenarioStatus.INFEASIBLE,
                    overrides=overrides,
                    financial_comparison_by_currency={},
                    operational_impact={},
                    limitations=limitations,
                )
            inv_mult *= overrides.lead_time_multiplier

        if overrides.freight_cost_multiplier is not None and overrides.freight_cost_multiplier >= 0.0:
            tco_mult *= overrides.freight_cost_multiplier

        if overrides.supplier_price_multiplier is not None and overrides.supplier_price_multiplier >= 0.0:
            tco_mult *= overrides.supplier_price_multiplier
            inv_mult *= overrides.supplier_price_multiplier

        for curr in all_currencies:
            curr_clean = curr.upper().strip()

            base_inv_val = base_inv_map.get(curr_clean)
            base_hold_val = base_hold_map.get(curr_clean)
            base_tco_val = base_tco_map.get(curr_clean)

            # Baseline TrackedValues
            base_inv_valid = base_inv_val is not None and base_inv_val >= 0.0
            base_inv_tv = TrackedValue(
                value=round(base_inv_val, 2) if base_inv_valid and base_inv_val is not None else None,
                state=ValueState.OBSERVED if base_inv_valid else ValueState.UNAVAILABLE,
                source="BASELINE_INVENTORY_VALUE" if base_inv_valid else "UNAVAILABLE",
            )

            base_hold_valid = base_hold_val is not None and base_hold_val >= 0.0
            base_hold_tv = TrackedValue(
                value=round(base_hold_val, 2) if base_hold_valid and base_hold_val is not None else None,
                state=ValueState.OBSERVED if base_hold_valid else ValueState.UNAVAILABLE,
                source="BASELINE_HOLDING_COST" if base_hold_valid else "UNAVAILABLE",
            )

            base_tco_valid = base_tco_val is not None and base_tco_val >= 0.0
            base_tco_tv = TrackedValue(
                value=round(base_tco_val, 2) if base_tco_valid and base_tco_val is not None else None,
                state=ValueState.OBSERVED if base_tco_valid else ValueState.UNAVAILABLE,
                source="BASELINE_TCO" if base_tco_valid else "UNAVAILABLE",
            )

            # Scenario Calculation (Non-Mutating Isolation)
            if base_inv_tv.value is not None:
                scen_inv_val = round(float(base_inv_tv.value) * inv_mult, 2)
                scen_inv_tv = TrackedValue(
                    value=scen_inv_val,
                    state=ValueState.DERIVED,
                    source="SCENARIO_INVENTORY_VALUE",
                )
                inv_delta_tv = TrackedValue(
                    value=round(scen_inv_val - float(base_inv_tv.value), 2),
                    state=ValueState.DERIVED,
                    source="SCENARIO_INVENTORY_DELTA",
                )

                scen_hold_val = round(scen_inv_val * cfg.annual_holding_rate, 2)
                scen_hold_tv = TrackedValue(
                    value=scen_hold_val,
                    state=ValueState.DERIVED,
                    source="SCENARIO_HOLDING_COST",
                )

                if base_hold_tv.value is not None:
                    old_hold = float(base_hold_tv.value)
                else:
                    old_hold = float(base_inv_tv.value) * cfg.annual_holding_rate

                hold_delta_tv = TrackedValue(
                    value=round(scen_hold_val - old_hold, 2),
                    state=ValueState.DERIVED,
                    source="SCENARIO_HOLDING_DELTA",
                )
            else:
                scen_inv_tv = TrackedValue(value=None, state=ValueState.UNAVAILABLE, source="UNAVAILABLE")
                inv_delta_tv = TrackedValue(value=None, state=ValueState.UNAVAILABLE, source="UNAVAILABLE")
                scen_hold_tv = TrackedValue(value=None, state=ValueState.UNAVAILABLE, source="UNAVAILABLE")
                hold_delta_tv = TrackedValue(value=None, state=ValueState.UNAVAILABLE, source="UNAVAILABLE")

            if base_tco_tv.value is not None:
                scen_tco_val = round(float(base_tco_tv.value) * tco_mult, 2)
                scen_tco_tv = TrackedValue(
                    value=scen_tco_val,
                    state=ValueState.DERIVED,
                    source="SCENARIO_TCO",
                )
                tco_delta_tv = TrackedValue(
                    value=round(scen_tco_val - float(base_tco_tv.value), 2),
                    state=ValueState.DERIVED,
                    source="SCENARIO_TCO_DELTA",
                )
            else:
                scen_tco_tv = TrackedValue(value=None, state=ValueState.UNAVAILABLE, source="UNAVAILABLE")
                tco_delta_tv = TrackedValue(value=None, state=ValueState.UNAVAILABLE, source="UNAVAILABLE")

            financial_comparisons[curr_clean] = ScenarioFinancialComparison(
                currency=curr_clean,
                baseline_inventory_value=base_inv_tv,
                scenario_inventory_value=scen_inv_tv,
                inventory_value_delta=inv_delta_tv,
                baseline_holding_cost=base_hold_tv,
                scenario_holding_cost=scen_hold_tv,
                holding_cost_delta=hold_delta_tv,
                baseline_tco=base_tco_tv,
                scenario_tco=scen_tco_tv,
                tco_delta=tco_delta_tv,
            )

        operational_impacts: Dict[str, TrackedValue] = {}
        if overrides.demand_multiplier is not None:
            operational_impacts["demand_multiplier"] = TrackedValue(
                value=round(overrides.demand_multiplier, 4),
                state=ValueState.OBSERVED,
                source="SCENARIO_OVERRIDE",
            )
        if overrides.lead_time_multiplier is not None:
            operational_impacts["lead_time_multiplier"] = TrackedValue(
                value=round(overrides.lead_time_multiplier, 4),
                state=ValueState.OBSERVED,
                source="SCENARIO_OVERRIDE",
            )

        return ScenarioResult(
            scenario_id=scenario_id,
            scenario_type=scenario_type,
            description=description,
            status=ScenarioStatus.COMPUTED,
            overrides=overrides,
            financial_comparison_by_currency=financial_comparisons,
            operational_impact=operational_impacts,
            limitations=limitations,
        )