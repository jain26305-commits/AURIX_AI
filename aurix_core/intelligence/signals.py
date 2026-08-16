"""Signal extraction engine for Phase 9 Executive Intelligence."""

import uuid
from typing import Dict, List, Optional
from aurix_core.intelligence.config import IntelligenceConfiguration
from aurix_core.schema.phase5_contract import TrackedValue, ValueState
from aurix_core.schema.phase8_contract import Phase8InputContract
from aurix_core.schema.phase9_contract import Phase9InputContract
from aurix_core.schema.phase10_contract import Phase10InputContract
from aurix_core.schema.phase11_contract import (
    BusinessSignal,
    EvidenceType,
    SignalDomain,
    SignalSeverity,
)


class SignalExtractor:
    """Extracts structured business signals from validated Phase 1-8 analytical contracts."""

    @classmethod
    def extract_signals(
        cls,
        phase7a_contract: Optional[Phase8InputContract] = None,
        phase7b_contract: Optional[Phase9InputContract] = None,
        phase8_contract: Optional[Phase10InputContract] = None,
        config: Optional[IntelligenceConfiguration] = None,
    ) -> List[BusinessSignal]:
        """Extracts structured BusinessSignal instances across network, decision, and economic domains."""
        cfg = config or IntelligenceConfiguration()
        signals: List[BusinessSignal] = []

        # 1. Extract Economic & Working Capital Signals (Phase 8)
        if phase8_contract:
            for sku_id, wc_list in phase8_contract.sku_working_capital.items():
                for wc in wc_list:
                    if wc.financial_risk_level.value in ("HIGH", "CRITICAL"):
                        severity = (
                            SignalSeverity.CRITICAL
                            if wc.financial_risk_level.value == "CRITICAL"
                            else SignalSeverity.HIGH
                        )
                        sig_id = f"SIG-ECON-{uuid.uuid4().hex[:8]}"

                        metrics: Dict[str, TrackedValue] = {
                            "total_inventory_value": wc.total_inventory_value,
                            "annual_holding_cost": wc.annual_holding_cost,
                        }

                        signals.append(
                            BusinessSignal(
                                signal_id=sig_id,
                                signal_type="HIGH_WORKING_CAPITAL_EXPOSURE",
                                domain=SignalDomain.ECONOMICS,
                                severity=severity,
                                affected_entity_id=f"{sku_id}@{wc.node_id}",
                                description=(
                                    f"SKU {sku_id} at {wc.node_id} has elevated working capital exposure "
                                    f"classified as {wc.financial_risk_level.value} risk."
                                ),
                                evidence_quality=EvidenceType.DERIVED,
                                source_phase="Phase 8",
                                source_metrics=metrics,
                                financial_exposure=wc.total_inventory_value,
                                provenance={"sku_id": sku_id, "node_id": wc.node_id},
                            )
                        )

        # 2. Extract Decision Engine Signals (Phase 7B)
        if phase7b_contract:
            for sku_id, opt_result in phase7b_contract.decisions.items():
                if opt_result.status.value == "RECOMMENDED" and opt_result.recommended_action:
                    rec = opt_result.recommended_action
                    sig_id = f"SIG-DEC-{uuid.uuid4().hex[:8]}"

                    metrics = {
                        "rebalance_quantity": TrackedValue(
                            value=rec.quantity,
                            state=ValueState.DERIVED,
                            source="RECOMMENDED_ACTION_QUANTITY",
                        ),
                        "coverage_improvement_days": rec.operational_impact.inventory_coverage_change_days,
                    }

                    signals.append(
                        BusinessSignal(
                            signal_id=sig_id,
                            signal_type="INVENTORY_REBALANCE_OPPORTUNITY",
                            domain=SignalDomain.DECISION,
                            severity=SignalSeverity.MODERATE,
                            affected_entity_id=f"{sku_id} ({rec.source_node}->{rec.destination_node})",
                            description=(
                                f"Validated opportunity to rebalance {rec.quantity:.1f} units of SKU {sku_id} "
                                f"from {rec.source_node} to {rec.destination_node}."
                            ),
                            evidence_quality=EvidenceType.RECOMMENDATION,
                            source_phase="Phase 7B",
                            source_metrics=metrics,
                            financial_exposure=rec.financial_impact.working_capital_released,
                            provenance={"recommendation_id": rec.recommendation_id, "sku_id": sku_id},
                        )
                    )

        # 3. Extract Network Topology & Vulnerability Signals (Phase 7A)
        if phase7a_contract:
            vulnerabilities = phase7a_contract.vulnerabilities
            for single_src in vulnerabilities.single_source_dependencies:
                sig_id = f"SIG-NET-{uuid.uuid4().hex[:8]}"

                if isinstance(single_src, dict):
                    desc = str(single_src.get("description", "Single source dependency detected."))
                    node_id = str(single_src.get("node_id", "UNKNOWN_NODE"))
                elif isinstance(single_src, str):
                    desc = f"Single source dependency detected for {single_src}."
                    node_id = single_src
                else:
                    desc = f"Single source dependency detected for {str(single_src)}."
                    node_id = str(single_src)

                signals.append(
                    BusinessSignal(
                        signal_id=sig_id,
                        signal_type="SINGLE_SOURCE_DEPENDENCY",
                        domain=SignalDomain.NETWORK,
                        severity=SignalSeverity.HIGH,
                        affected_entity_id=node_id,
                        description=desc,
                        evidence_quality=EvidenceType.OBSERVED,
                        source_phase="Phase 7A",
                        source_metrics={},
                        financial_exposure=None,
                        provenance={"node_id": node_id},
                    )
                )

            for imb in phase7a_contract.inventory_imbalances:
                if imb.imbalance_detected:
                    sig_id = f"SIG-NET-IMB-{uuid.uuid4().hex[:8]}"

                    signals.append(
                        BusinessSignal(
                            signal_id=sig_id,
                            signal_type="NETWORK_INVENTORY_IMBALANCE",
                            domain=SignalDomain.NETWORK,
                            severity=SignalSeverity.MODERATE,
                            affected_entity_id=imb.sku_id,
                            description=imb.description,
                            evidence_quality=EvidenceType.OBSERVED,
                            source_phase="Phase 7A",
                            source_metrics={},
                            financial_exposure=None,
                            provenance={"sku_id": imb.sku_id},
                        )
                    )

        # Cap signals per domain according to configuration limit
        domain_counts: Dict[SignalDomain, int] = {}
        filtered_signals: List[BusinessSignal] = []

        for sig in signals:
            curr_count = domain_counts.get(sig.domain, 0)
            if curr_count < cfg.max_signals_per_domain:
                filtered_signals.append(sig)
                domain_counts[sig.domain] = curr_count + 1

        return filtered_signals