"""Financial Intelligence & Supply Chain Economics Engine (Phase 8)."""

from typing import Any, Dict, List, Optional
from aurix_core.economics.config import EconomicsConfiguration
from aurix_core.schema.phase5_contract import TrackedValue, ValueState
from aurix_core.schema.phase10_contract import (
    CurrencyGroupedPortfolio,
    FinancialRiskLevel,
    TCOBreakdown,
    WorkingCapitalExposure,
)


class FinancialEngine:
    """Calculates working capital exposure, TCO breakdowns, and currency-isolated portfolio metrics."""

    @classmethod
    def calculate_working_capital(
        cls,
        sku_id: str,
        node_id: str,
        on_hand_units: Optional[float],
        cycle_stock_units: Optional[float] = None,
        safety_stock_units: Optional[float] = None,
        excess_units: Optional[float] = None,
        unit_cost: Optional[float] = None,
        currency: Optional[str] = None,
        config: Optional[EconomicsConfiguration] = None,
    ) -> WorkingCapitalExposure:
        """Calculates working capital segmentation and annual holding cost for a SKU at a specific node."""
        cfg = config or EconomicsConfiguration()
        clean_curr = (currency or cfg.default_currency).upper().strip()

        has_cost = unit_cost is not None and unit_cost >= 0.0

        def _build_value(units: Optional[float], source_tag: str) -> TrackedValue:
            if has_cost and units is not None and units >= 0.0:
                assert unit_cost is not None
                return TrackedValue(
                    value=round(units * unit_cost, 2),
                    state=ValueState.DERIVED,
                    source=source_tag,
                )
            return TrackedValue(
                value=None,
                state=ValueState.UNAVAILABLE,
                source="MISSING_UNIT_COST_OR_QUANTITY",
            )

        total_inv_tv = _build_value(on_hand_units, "TOTAL_INVENTORY_VALUE")
        cycle_val_tv = _build_value(cycle_stock_units, "CYCLE_STOCK_VALUE")
        safety_val_tv = _build_value(safety_stock_units, "SAFETY_STOCK_VALUE")
        excess_val_tv = _build_value(excess_units, "EXCESS_CAPITAL_VALUE")

        # Holding Cost Calculation
        if total_inv_tv.value is not None and total_inv_tv.value >= 0.0:
            holding_cost = round(float(total_inv_tv.value) * cfg.annual_holding_rate, 2)
            holding_cost_tv = TrackedValue(
                value=holding_cost,
                state=ValueState.DERIVED,
                source="ANNUAL_HOLDING_COST_CALCULATION",
            )
        else:
            holding_cost_tv = TrackedValue(
                value=None,
                state=ValueState.UNAVAILABLE,
                source="MISSING_INVENTORY_VALUE",
            )

        # Financial Risk Level Classification
        if total_inv_tv.value is None:
            risk_level = FinancialRiskLevel.UNAVAILABLE
        elif total_inv_tv.value <= cfg.financial_risk_low_max:
            risk_level = FinancialRiskLevel.LOW
        elif total_inv_tv.value <= cfg.financial_risk_moderate_max:
            risk_level = FinancialRiskLevel.MODERATE
        elif total_inv_tv.value <= cfg.financial_risk_high_max:
            risk_level = FinancialRiskLevel.HIGH
        else:
            risk_level = FinancialRiskLevel.CRITICAL

        return WorkingCapitalExposure(
            sku_id=sku_id,
            node_id=node_id,
            currency=clean_curr,
            total_inventory_value=total_inv_tv,
            cycle_stock_value=cycle_val_tv,
            safety_stock_value=safety_val_tv,
            excess_capital_tied=excess_val_tv,
            annual_holding_cost=holding_cost_tv,
            financial_risk_level=risk_level,
        )

    @classmethod
    def calculate_tco(
        cls,
        purchase_cost: Optional[TrackedValue] = None,
        freight_cost: Optional[TrackedValue] = None,
        holding_cost: Optional[TrackedValue] = None,
        expedite_cost: Optional[TrackedValue] = None,
        stockout_cost: Optional[TrackedValue] = None,
        currency: str = "USD",
    ) -> TCOBreakdown:
        """Calculates Total Cost of Ownership by transparently summing available cost components."""
        clean_curr = currency.upper().strip()

        components = [purchase_cost, freight_cost, holding_cost, expedite_cost, stockout_cost]
        valid_values = [
            float(c.value) for c in components if c is not None and c.value is not None and float(c.value) >= 0.0
        ]

        def _ensure_tv(tv: Optional[TrackedValue], default_source: str) -> TrackedValue:
            if tv is None:
                return TrackedValue(value=None, state=ValueState.UNAVAILABLE, source=default_source)
            return tv

        p_tv = _ensure_tv(purchase_cost, "PURCHASE_COST_UNAVAILABLE")
        f_tv = _ensure_tv(freight_cost, "FREIGHT_COST_UNAVAILABLE")
        h_tv = _ensure_tv(holding_cost, "HOLDING_COST_UNAVAILABLE")
        e_tv = _ensure_tv(expedite_cost, "EXPEDITE_COST_UNAVAILABLE")
        s_tv = _ensure_tv(stockout_cost, "STOCKOUT_COST_UNAVAILABLE")

        if valid_values:
            total_tco = TrackedValue(
                value=round(sum(valid_values), 2),
                state=ValueState.DERIVED,
                source="SUM_OF_AVAILABLE_TCO_COMPONENTS",
            )
        else:
            total_tco = TrackedValue(
                value=None,
                state=ValueState.UNAVAILABLE,
                source="ALL_TCO_COMPONENTS_UNAVAILABLE",
            )

        return TCOBreakdown(
            currency=clean_curr,
            purchase_cost=p_tv,
            freight_cost=f_tv,
            holding_cost=h_tv,
            expedite_cost=e_tv,
            stockout_exposure_cost=s_tv,
            total_cost_of_ownership=total_tco,
        )

    @classmethod
    def aggregate_portfolio_by_currency(
        cls,
        exposures: List[WorkingCapitalExposure],
        freight_records: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, CurrencyGroupedPortfolio]:
        """Aggregates portfolio financial metrics strictly grouped by native currency."""
        currency_groups: Dict[str, Dict[str, Any]] = {}

        for exp in exposures:
            curr = exp.currency
            if curr not in currency_groups:
                currency_groups[curr] = {
                    "inv_val": 0.0,
                    "holding_cost": 0.0,
                    "freight_spend": 0.0,
                    "has_inv_val": False,
                    "has_holding_cost": False,
                    "has_freight": False,
                }

            if exp.total_inventory_value.value is not None:
                currency_groups[curr]["inv_val"] += float(exp.total_inventory_value.value)
                currency_groups[curr]["has_inv_val"] = True

            if exp.annual_holding_cost.value is not None:
                currency_groups[curr]["holding_cost"] += float(exp.annual_holding_cost.value)
                currency_groups[curr]["has_holding_cost"] = True

        if freight_records:
            for rec in freight_records:
                curr = str(rec.get("currency", "USD")).upper().strip()
                amt = rec.get("amount")
                if curr not in currency_groups:
                    currency_groups[curr] = {
                        "inv_val": 0.0,
                        "holding_cost": 0.0,
                        "freight_spend": 0.0,
                        "has_inv_val": False,
                        "has_holding_cost": False,
                        "has_freight": False,
                    }
                if amt is not None and float(amt) >= 0.0:
                    currency_groups[curr]["freight_spend"] += float(amt)
                    currency_groups[curr]["has_freight"] = True

        portfolio_by_currency: Dict[str, CurrencyGroupedPortfolio] = {}
        for curr, metrics in currency_groups.items():
            inv_tv = TrackedValue(
                value=round(metrics["inv_val"], 2) if metrics["has_inv_val"] else None,
                state=ValueState.DERIVED if metrics["has_inv_val"] else ValueState.UNAVAILABLE,
                source="PORTFOLIO_AGGREGATED_INVENTORY_VALUE" if metrics["has_inv_val"] else "UNAVAILABLE",
            )
            holding_tv = TrackedValue(
                value=round(metrics["holding_cost"], 2) if metrics["has_holding_cost"] else None,
                state=ValueState.DERIVED if metrics["has_holding_cost"] else ValueState.UNAVAILABLE,
                source="PORTFOLIO_AGGREGATED_HOLDING_COST" if metrics["has_holding_cost"] else "UNAVAILABLE",
            )
            freight_tv = TrackedValue(
                value=round(metrics["freight_spend"], 2) if metrics["has_freight"] else None,
                state=ValueState.DERIVED if metrics["has_freight"] else ValueState.UNAVAILABLE,
                source="PORTFOLIO_AGGREGATED_FREIGHT_SPEND" if metrics["has_freight"] else "UNAVAILABLE",
            )

            portfolio_by_currency[curr] = CurrencyGroupedPortfolio(
                currency=curr,
                total_inventory_value=inv_tv,
                total_working_capital_exposure=inv_tv,
                total_holding_cost=holding_tv,
                total_freight_spend=freight_tv,
            )

        return portfolio_by_currency