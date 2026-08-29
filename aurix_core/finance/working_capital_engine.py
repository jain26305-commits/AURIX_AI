"""
AURIX Business Finance Intelligence — Working Capital & CCC Engine
Phase 21 Core Implementation.
Calculates Operating Working Capital and Cash Conversion Cycle (CCC) with driver attribution.
"""

from __future__ import annotations

from typing import Any, Dict, List
from aurix_core.finance.contracts import WorkingCapitalSummary


class WorkingCapitalEngine:
    """Calculates Working Capital and Cash Conversion Cycle (CCC)."""

    @classmethod
    def calculate_working_capital(
        cls,
        tenant_id: str,
        inventory_valuation: float,
        accounts_receivable: float,
        accounts_payable: float,
        annual_revenue: float,
        annual_cogs: float,
        days_in_period: int = 365,
        currency: str = "USD",
    ) -> WorkingCapitalSummary:
        """
        Operating Working Capital = Inventory + AR - AP
        CCC = DSO + DIO - DPO
        DIO = (Inventory / COGS) * Days
        DSO = (AR / Revenue) * Days
        DPO = (AP / COGS) * Days
        """
        owc = round(inventory_valuation + accounts_receivable - accounts_payable, 2)

        dso = round((accounts_receivable / max(1.0, annual_revenue)) * days_in_period, 1)
        dio = round((inventory_valuation / max(1.0, annual_cogs)) * days_in_period, 1)
        dpo = round((accounts_payable / max(1.0, annual_cogs)) * days_in_period, 1)

        ccc = round(dso + dio - dpo, 1)

        # Driver Decomposition & Attribution
        drivers = [
            {
                "driver": "Inventory Holding Growth",
                "days_impact": dio,
                "capital_impact": inventory_valuation,
                "direction": "UNFAVORABLE" if dio > 45 else "FAVORABLE",
            },
            {
                "driver": "Customer Receivable Days (DSO)",
                "days_impact": dso,
                "capital_impact": accounts_receivable,
                "direction": "UNFAVORABLE" if dso > 40 else "FAVORABLE",
            },
            {
                "driver": "Supplier Payment Terms (DPO)",
                "days_impact": -dpo,
                "capital_impact": -accounts_payable,
                "direction": "FAVORABLE" if dpo >= 30 else "UNFAVORABLE",
            },
        ]

        return WorkingCapitalSummary(
            tenant_id=tenant_id,
            currency=currency,
            inventory_valuation=round(inventory_valuation, 2),
            accounts_receivable=round(accounts_receivable, 2),
            accounts_payable=round(accounts_payable, 2),
            operating_working_capital=owc,
            dso_days=dso,
            dio_days=dio,
            dpo_days=dpo,
            cash_conversion_cycle_days=ccc,
            driver_attribution=drivers,
        )
