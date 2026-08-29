"""
AURIX Continuous Assurance — Phantom Inventory & Shrinkage Audit Engine
Phase 20 Core Implementation.
Flags variances between physical cycle counts and recorded book stock.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from aurix_core.assurance.contracts import (
    AssuranceDomain,
    AssuranceFinding,
    LeakageSeverity,
)


class PhantomInventoryEngine:
    """Audits book inventory positions against physical counts and negative stocks."""

    @classmethod
    def evaluate_inventory(
        cls,
        tenant_id: str,
        positions: List[Dict[str, Any]],
        cycle_counts: Optional[List[Dict[str, Any]]] = None,
    ) -> List[AssuranceFinding]:
        """Identifies negative stocks, phantom records, and physical count shortfalls."""
        findings: List[AssuranceFinding] = []

        # 1. Negative on-hand detection
        for pos in positions:
            sku_id = str(pos.get("sku_id") or pos.get("sku") or "")
            loc_id = str(pos.get("location_id") or pos.get("warehouse_id") or "")
            on_hand = float(pos.get("on_hand") or pos.get("quantity") or 0.0)
            unit_cost = float(pos.get("unit_cost") or pos.get("cost_price") or 10.0)

            if on_hand < 0:
                exposure = round(abs(on_hand) * unit_cost, 2)
                finding = AssuranceFinding(
                    tenant_id=tenant_id,
                    domain=AssuranceDomain.PHANTOM_INVENTORY,
                    severity=LeakageSeverity.HIGH,
                    title=f"Negative Inventory Balance: SKU {sku_id}",
                    description=f"Location {loc_id} reports negative balance of {on_hand} units.",
                    financial_exposure=exposure,
                    entity_type="inventory_position",
                    entity_id=f"{sku_id}@{loc_id}",
                    evidence_data={"on_hand": on_hand, "unit_cost": unit_cost, "location": loc_id},
                    recommended_action="Perform immediate cycle count to adjust ghost inventory balance.",
                )
                findings.append(finding)

        # 2. Cycle count shrinkage audit
        if cycle_counts:
            for count in cycle_counts:
                sku_id = str(count.get("sku_id") or "")
                loc_id = str(count.get("location_id") or "")
                book_qty = float(count.get("book_quantity") or count.get("expected_qty") or 0.0)
                phys_qty = float(count.get("physical_quantity") or count.get("actual_qty") or 0.0)
                unit_cost = float(count.get("unit_cost") or 10.0)

                variance_qty = phys_qty - book_qty
                if variance_qty < 0:  # Physical count is less than book stock (Shrinkage)
                    loss_amount = round(abs(variance_qty) * unit_cost, 2)
                    severity = LeakageSeverity.CRITICAL if loss_amount > 5000 else (LeakageSeverity.HIGH if loss_amount > 1000 else LeakageSeverity.MEDIUM)
                    finding = AssuranceFinding(
                        tenant_id=tenant_id,
                        domain=AssuranceDomain.PHANTOM_INVENTORY,
                        severity=severity,
                        title=f"Physical Shrinkage Variance: SKU {sku_id}",
                        description=f"Physical count ({phys_qty}) is {abs(variance_qty)} units below book record ({book_qty}).",
                        financial_exposure=loss_amount,
                        entity_type="inventory_position",
                        entity_id=f"{sku_id}@{loc_id}",
                        evidence_data={"book_qty": book_qty, "physical_qty": phys_qty, "shrinkage_units": abs(variance_qty), "unit_cost": unit_cost},
                        recommended_action="Post write-off adjustment and trigger warehouse security investigation.",
                    )
                    findings.append(finding)

        return findings
