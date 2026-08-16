"""Master Orchestrator for Phase 7B Multi-Echelon Optimization & Network Decision Engine."""

import datetime
import uuid
from typing import Any, Dict, List, Optional, Tuple
from aurix_core.decision.config import DecisionConfiguration
from aurix_core.decision.rebalancing import InventoryRebalancer
from aurix_core.decision.tradeoff import TradeoffEvaluator
from aurix_core.schema.phase5_contract import MissingInput, TrackedValue, ValueState
from aurix_core.schema.phase8_contract import NetworkEdge, NodeIdentity, Phase8InputContract
from aurix_core.schema.phase9_contract import (
    DecisionRecommendation,
    FinancialImpact,
    OptimizationResult,
    OptimizationStatus,
    Phase9InputContract,
)

__all__ = ["Phase7BOrchestrator"]


class Phase7BOrchestrator:
    """Master Orchestrator for Phase 7B Multi-Echelon Optimization & Network Decision Engine."""

    def __init__(
        self,
        phase7a_network_output: Optional[Dict[str, Any]] = None,
        unit_cost_by_sku: Optional[Dict[str, float]] = None,
        target_coverage_days_by_node: Optional[Dict[str, float]] = None,
        config_override: Optional[Any] = None,
    ) -> None:
        self.phase7a_data = phase7a_network_output or {}
        self.unit_cost_by_sku = unit_cost_by_sku or {}
        self.target_coverage_by_node = target_coverage_days_by_node or {}

        if isinstance(config_override, DecisionConfiguration):
            self.config = config_override
        elif isinstance(config_override, dict):
            self.config = DecisionConfiguration(config_override)
        else:
            self.config = DecisionConfiguration()

        self.run_id = str(uuid.uuid4())
        self.timestamp = datetime.datetime.now().isoformat()

    def execute(self) -> Dict[str, Any]:
        """Executes the complete Phase 7B optimization pipeline and returns dictionary output."""
        contract = self.process_optimization()
        return contract.model_dump()

    def process_optimization(self) -> Phase9InputContract:
        """Processes Phase 7A network contracts and executes multi-echelon optimization."""
        missing_inputs: List[MissingInput] = []
        limitations: List[str] = []
        decisions: Dict[str, OptimizationResult] = {}

        # 1. Parse Phase 7A Network Contract
        if not self.phase7a_data:
            missing_inputs.append(
                MissingInput(
                    field="phase7a_network_output",
                    state="USER_INPUT_REQUIRED",
                    domain="decision",
                    severity="CRITICAL",
                    prompt="No Phase 7A network foundation data provided.",
                )
            )
            empty_financial = FinancialImpact(
                total_cost_change=TrackedValue(value=None, state=ValueState.UNAVAILABLE, source="UNAVAILABLE"),
                working_capital_released=TrackedValue(value=None, state=ValueState.UNAVAILABLE, source="UNAVAILABLE"),
                transportation_cost_change=TrackedValue(
                    value=None, state=ValueState.UNAVAILABLE, source="UNAVAILABLE"
                ),
            )
            return Phase9InputContract(
                status="USER_INPUT_REQUIRED",
                missing_inputs=missing_inputs,
                decisions={},
                portfolio_financial_impact=empty_financial,
                limitations=["MISSING_PHASE7A_NETWORK_INPUTS"],
                provenance={
                    "phase7b_run_id": self.run_id,
                    "timestamp": self.timestamp,
                    "engine_version": "7.5.0-decision-engine",
                },
            )

        p7a_contract = Phase8InputContract(**self.phase7a_data)
        nodes: Dict[str, NodeIdentity] = p7a_contract.nodes
        edges: List[NetworkEdge] = p7a_contract.edges
        imbalances = p7a_contract.inventory_imbalances

        if not nodes or not edges:
            limitations.append("Network graph contains no valid nodes or edges to optimize.")

        # Map edges by (src, dst, sku) using uppercase Tuple for compatibility
        edge_map: Dict[Tuple[str, str, str], NetworkEdge] = {
            (e.source_node_id, e.destination_node_id, e.sku_id): e for e in edges
        }

        # 2. Process Inventory Imbalances & Rebalancing Opportunities
        for imb in imbalances:
            sku = imb.sku_id
            sku_nodes = imb.nodes_compared
            unit_cost = self.unit_cost_by_sku.get(sku)

            evaluations: List[DecisionRecommendation] = []

            for src_id in sku_nodes:
                for dst_id in sku_nodes:
                    if src_id == dst_id:
                        continue

                    edge = edge_map.get((src_id, dst_id, sku))
                    if not edge:
                        continue

                    src_node = nodes.get(src_id)
                    dst_node = nodes.get(dst_id)

                    src_target = self.target_coverage_by_node.get(src_id, 20.0)
                    dst_target = self.target_coverage_by_node.get(dst_id, 20.0)

                    result = InventoryRebalancer.evaluate_rebalance(
                        source_node=src_node,
                        dest_node=dst_node,
                        edge=edge,
                        source_target_coverage_days=src_target,
                        dest_target_coverage_days=dst_target,
                        unit_cost=unit_cost,
                        config=self.config,
                    )

                    if result.status == OptimizationStatus.RECOMMENDED and result.recommended_action:
                        evaluations.append(result.recommended_action)

            # 3. Select Primary Action & Trade-off Alternatives
            if evaluations:
                # Rank by coverage improvement delta descending
                evaluations.sort(
                    key=lambda r: float(r.operational_impact.inventory_coverage_change_days.value or 0.0),
                    reverse=True,
                )
                primary = evaluations[0]
                alts_raw = evaluations[1 : self.config.max_recommendations_per_sku]

                tradeoffs = TradeoffEvaluator.compare_recommendations(primary, alts_raw)

                decisions[sku] = OptimizationResult(
                    status=OptimizationStatus.RECOMMENDED,
                    reason=(
                        f"Generated primary rebalancing recommendation and {len(tradeoffs)} "
                        f"alternative trade-off options for SKU {sku}."
                    ),
                    recommended_action=primary,
                    alternatives=tradeoffs,
                    limitations=[],
                )
            else:
                decisions[sku] = OptimizationResult(
                    status=OptimizationStatus.NOT_OPTIMIZABLE,
                    reason=(
                        f"SKU {sku} has an inventory imbalance but no feasible, validated transfer route "
                        "met the minimum improvement gates."
                    ),
                    recommended_action=None,
                    alternatives=[],
                    limitations=[f"No feasible transfer edge passed the improvement gate for SKU {sku}."],
                )

        # 4. Portfolio Financial Aggregation
        total_transport_cost = 0.0
        total_working_cap_released = 0.0
        has_valid_financials = False

        for res in decisions.values():
            if res.status == OptimizationStatus.RECOMMENDED and res.recommended_action:
                fin = res.recommended_action.financial_impact
                if fin.total_cost_change and fin.total_cost_change.value is not None:
                    total_transport_cost += float(fin.total_cost_change.value)
                    has_valid_financials = True

                if fin.working_capital_released and fin.working_capital_released.value is not None:
                    total_working_cap_released += float(fin.working_capital_released.value)
                    has_valid_financials = True

        portfolio_financial = FinancialImpact(
            total_cost_change=TrackedValue(
                value=round(total_transport_cost, 2) if has_valid_financials else None,
                state=ValueState.DERIVED if has_valid_financials else ValueState.UNAVAILABLE,
                source="PORTFOLIO_AGGREGATED_TRANSPORT_COST" if has_valid_financials else "UNAVAILABLE",
            ),
            working_capital_released=TrackedValue(
                value=round(total_working_cap_released, 2) if has_valid_financials else None,
                state=ValueState.DERIVED if has_valid_financials else ValueState.UNAVAILABLE,
                source="PORTFOLIO_AGGREGATED_WORKING_CAPITAL" if has_valid_financials else "UNAVAILABLE",
            ),
            transportation_cost_change=TrackedValue(
                value=round(total_transport_cost, 2) if has_valid_financials else None,
                state=ValueState.DERIVED if has_valid_financials else ValueState.UNAVAILABLE,
                source="PORTFOLIO_AGGREGATED_TRANSPORT_COST" if has_valid_financials else "UNAVAILABLE",
            ),
            currency="USD",
        )

        overall_status = "COMPUTABLE" if decisions else "NO_OPTIMIZATIONS_FOUND"

        return Phase9InputContract(
            status=overall_status,
            missing_inputs=missing_inputs,
            decisions=decisions,
            portfolio_financial_impact=portfolio_financial,
            limitations=limitations,
            provenance={
                "phase7b_run_id": self.run_id,
                "phase7a_run_id": p7a_contract.provenance.get("phase7a_run_id", "UNKNOWN"),
                "timestamp": self.timestamp,
                "engine_version": "7.5.0-decision-engine",
            },
        )