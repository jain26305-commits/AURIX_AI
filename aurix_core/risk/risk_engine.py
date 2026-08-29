"""
AURIX Risk, Causal & External Intelligence — Enterprise Risk Engine
Phase 26 Core Implementation.
Evaluates cross-domain operational and commercial risks (Supplier, Customer, SKU, Inventory, Plant, Finance, Mfg, Process).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from aurix_core.risk.contracts import (
    RiskDomain,
    RiskFinding,
    RiskSeverity,
    RiskStatus,
)


class RiskEngine:
    """Evaluates cross-domain enterprise risks from authoritative operational signals."""

    @classmethod
    def evaluate_risks(
        cls,
        tenant_id: str,
        suppliers: List[Dict[str, Any]],
        customers: List[Dict[str, Any]],
        inventory_items: List[Dict[str, Any]],
        work_orders: List[Dict[str, Any]],
        assurance_findings: List[Dict[str, Any]],
        process_bottlenecks: List[Dict[str, Any]],
        external_signal_mappings: Optional[List[Dict[str, Any]]] = None,
    ) -> List[RiskFinding]:
        """Scan multi-domain operating telemetry and generate discrete, evidence-backed risk findings."""
        findings: List[RiskFinding] = []
        now = datetime.now(timezone.utc)

        # 1. Supplier Delivery & Performance Risk
        for s in suppliers:
            s_id = str(s.get("id") or s.get("supplier_id"))
            otif = float(s.get("otif_rate") or 100.0)
            spend = float(s.get("annual_spend") or 50000.0)

            if otif < 85.0:
                prob = round(min(0.95, (100.0 - otif) / 100.0 * 1.5), 2)
                exp_loss = round(prob * spend * 0.15, 2)

                findings.append(
                    RiskFinding(
                        tenant_id=tenant_id,
                        risk_domain=RiskDomain.SUPPLIER,
                        entity_type="SUPPLIER",
                        entity_id=s_id,
                        title=f"Supplier Reliability Deficit: {s.get('supplier_name', s_id)}",
                        description=f"Supplier OTIF rate ({otif:.1f}%) is below operational threshold (85%).",
                        probability=prob,
                        impact_amount_usd=spend * 0.15,
                        exposure_amount_usd=exp_loss,
                        urgency_hours=48.0,
                        severity=RiskSeverity.HIGH if otif < 70.0 else RiskSeverity.MEDIUM,
                        evidence={"otif_rate": otif, "spend": spend},
                    )
                )

        # 2. Customer Credit & Dormancy Risk
        for c in customers:
            c_id = str(c.get("id") or c.get("customer_id"))
            health = float(c.get("health_score") or 100.0)
            rev = float(c.get("period_revenue") or 25000.0)

            if health < 60.0:
                prob = round(min(0.90, (100.0 - health) / 100.0), 2)
                exp_loss = round(prob * rev, 2)

                findings.append(
                    RiskFinding(
                        tenant_id=tenant_id,
                        risk_domain=RiskDomain.CUSTOMER,
                        entity_type="CUSTOMER",
                        entity_id=c_id,
                        title=f"Customer Defection Risk: {c.get('customer_name', c_id)}",
                        description=f"Account health score ({health:.1f}) indicates high dormancy or churn probability.",
                        probability=prob,
                        impact_amount_usd=rev,
                        exposure_amount_usd=exp_loss,
                        urgency_hours=24.0,
                        severity=RiskSeverity.CRITICAL if health < 40.0 else RiskSeverity.HIGH,
                        evidence={"health_score": health, "period_revenue": rev},
                    )
                )

        # 3. Manufacturing Bottleneck & Schedule Risk
        for wo in work_orders:
            wo_id = str(wo.get("id") or wo.get("work_order_number"))
            status = str(wo.get("status") or "").upper()
            target_qty = float(wo.get("target_quantity") or 100.0)
            completed_qty = float(wo.get("completed_quantity") or 0.0)

            if status in ("CONSTRAINED", "DELAYED") or (completed_qty == 0.0 and status == "IN_PROGRESS"):
                findings.append(
                    RiskFinding(
                        tenant_id=tenant_id,
                        risk_domain=RiskDomain.MANUFACTURING,
                        entity_type="WORK_ORDER",
                        entity_id=wo_id,
                        title=f"Work Order Execution Stoppage: {wo_id}",
                        description=f"Work order is constrained with {target_qty - completed_qty:.0f} units remaining unfulfilled.",
                        probability=0.75,
                        impact_amount_usd=target_qty * 120.0,
                        exposure_amount_usd=(target_qty * 120.0) * 0.75,
                        urgency_hours=12.0,
                        severity=RiskSeverity.HIGH,
                        evidence={"work_order_status": status, "target_quantity": target_qty},
                    )
                )

        # 4. External Signal Enrichment Linkage
        if external_signal_mappings:
            for mapping in external_signal_mappings:
                e_id = str(mapping.get("entity_id"))
                for finding in findings:
                    if finding.entity_id == e_id:
                        finding.probability = min(1.0, round(finding.probability * 1.25, 2))
                        finding.exposure_amount_usd = round(finding.probability * finding.impact_amount_usd, 2)
                        finding.evidence["external_signal_enrichment"] = mapping.get("mapping_rule")

        return findings
