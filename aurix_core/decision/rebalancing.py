"""Inventory rebalancing domain engine for evaluating node-to-node transfers and impact deltas."""

import uuid
from typing import Optional
from aurix_core.decision.baseline import BaselineEngine
from aurix_core.decision.config import DecisionConfiguration
from aurix_core.decision.gate import OptimizationGate
from aurix_core.decision.solver import ConstraintSatisfactionSolver
from aurix_core.schema.phase5_contract import TrackedValue, ValueState
from aurix_core.schema.phase8_contract import NetworkEdge, NodeIdentity
from aurix_core.schema.phase9_contract import (
    DecisionRecommendation,
    DecisionType,
    FinancialImpact,
    OperationalImpact,
    OptimizationResult,
    OptimizationStatus,
    OptimizedState,
)


class InventoryRebalancer:
    """Evaluates node-to-node inventory rebalancing opportunities and computes trade-off deltas."""

    @classmethod
    def evaluate_rebalance(
        cls,
        source_node: Optional[NodeIdentity],
        dest_node: Optional[NodeIdentity],
        edge: Optional[NetworkEdge] = None,
        source_target_coverage_days: float = 20.0,
        dest_target_coverage_days: float = 20.0,
        unit_cost: Optional[float] = None,
        pack_size: Optional[float] = None,
        config: Optional[DecisionConfiguration] = None,
    ) -> OptimizationResult:
        cfg = config or DecisionConfiguration()

        # 1. Readiness Gate Validation
        is_ready, gate_status, gate_reason = OptimizationGate.check_rebalancing_readiness(
            source_node=source_node,
            dest_node=dest_node,
            edge=edge,
        )
        if not is_ready:
            return OptimizationResult(
                status=gate_status,
                reason=gate_reason,
                recommended_action=None,
                alternatives=[],
                limitations=[gate_reason],
            )

        assert source_node is not None and dest_node is not None and edge is not None

        # 2. Baseline Evaluation
        dst_baseline = BaselineEngine.evaluate_node_baseline(
            dest_node, unit_cost, dest_target_coverage_days
        )

        src_inv = float(source_node.inventory.value)  # type: ignore[arg-type]
        src_demand = (
            float(source_node.demand.value)
            if (source_node.demand and source_node.demand.value is not None)
            else 0.0
        )

        dst_inv = float(dest_node.inventory.value)  # type: ignore[arg-type]
        dst_demand = (
            float(dest_node.demand.value)
            if (dest_node.demand and dest_node.demand.value is not None)
            else 0.0
        )

        # Calculate Excess at Source and Shortage at Destination
        src_required_inv = src_demand * source_target_coverage_days
        src_excess = max(0.0, src_inv - src_required_inv)

        dst_required_inv = dst_demand * dest_target_coverage_days
        dst_shortage = max(0.0, dst_required_inv - dst_inv)

        if src_excess <= 0.0:
            return OptimizationResult(
                status=OptimizationStatus.NO_IMPROVEMENT,
                reason=(
                    f"Source node {source_node.node_id} has no excess inventory above its target coverage of "
                    f"{source_target_coverage_days:.1f} days."
                ),
                recommended_action=None,
                alternatives=[],
                limitations=[],
            )

        if dst_shortage <= 0.0:
            return OptimizationResult(
                status=OptimizationStatus.NO_IMPROVEMENT,
                reason=(
                    f"Destination node {dest_node.node_id} currently meets or exceeds its target coverage of "
                    f"{dest_target_coverage_days:.1f} days."
                ),
                recommended_action=None,
                alternatives=[],
                limitations=[],
            )

        # 3. Constraint-Satisfaction Solver Execution
        dst_capacity = (
            float(dest_node.capacity.value)
            if (dest_node.capacity and dest_node.capacity.value is not None)
            else None
        )

        transfer_qty, feasibility, solver_logs = ConstraintSatisfactionSolver.solve_rebalancing_quantity(
            source_available_excess=src_excess,
            destination_shortage=dst_shortage,
            destination_available_capacity=dst_capacity,
            pack_size=pack_size,
            min_transfer_quantity=cfg.min_transfer_quantity,
        )

        if transfer_qty <= 0.0:
            return OptimizationResult(
                status=OptimizationStatus.INFEASIBLE,
                reason=f"Constraint solver determined zero feasible transfer quantity. Status: {feasibility.value}",
                recommended_action=None,
                alternatives=[],
                limitations=solver_logs,
            )

        # 4. Compute Post-Optimization States & Deltas
        new_dst_inv = dst_inv + transfer_qty
        new_dst_cov = (new_dst_inv / dst_demand) if dst_demand > 0.0 else float('inf')
        old_dst_cov = (
            float(dst_baseline.coverage_days.value)
            if (dst_baseline.coverage_days and dst_baseline.coverage_days.value is not None)
            else 0.0
        )

        cov_improvement_days = round(new_dst_cov - old_dst_cov, 2) if new_dst_cov != float('inf') else float('inf')

        # Improvement Gate Check
        if cov_improvement_days != float('inf') and cov_improvement_days < cfg.min_coverage_improvement_days:
            return OptimizationResult(
                status=OptimizationStatus.NO_IMPROVEMENT,
                reason=(
                    f"Projected coverage improvement of {cov_improvement_days:.2f} days is below the required "
                    f"threshold of {cfg.min_coverage_improvement_days:.2f} days."
                ),
                recommended_action=None,
                alternatives=[],
                limitations=solver_logs,
            )

        # 5. Operational & Financial Impact
        op_cov_change_tv = TrackedValue(
            value=cov_improvement_days if cov_improvement_days != float('inf') else None,
            state=ValueState.DERIVED,
            source="POST_REBALANCE_COVERAGE_DELTA",
        )

        old_dst_risk = (
            float(dst_baseline.service_exposure_risk.value)
            if (dst_baseline.service_exposure_risk and dst_baseline.service_exposure_risk.value is not None)
            else 0.0
        )
        new_dst_risk = (
            round(max(0.0, min(1.0, 1.0 - (new_dst_cov / dest_target_coverage_days))), 2)
            if (dest_target_coverage_days > 0.0 and new_dst_cov != float('inf'))
            else 0.0
        )
        risk_reduction = round(old_dst_risk - new_dst_risk, 2)

        op_stockout_change_tv = TrackedValue(
            value=-risk_reduction,
            state=ValueState.DERIVED,
            source="POST_REBALANCE_RISK_DELTA",
        )

        lead_time_val = (
            float(edge.lead_time_days.value)
            if (edge.lead_time_days and edge.lead_time_days.value is not None)
            else None
        )
        lead_time_tv = TrackedValue(
            value=lead_time_val,
            state=ValueState.OBSERVED if lead_time_val is not None else ValueState.UNAVAILABLE,
            source="EDGE_LEAD_TIME" if lead_time_val is not None else "UNAVAILABLE",
        )

        operational_impact = OperationalImpact(
            inventory_coverage_change_days=op_cov_change_tv,
            stockout_exposure_change=op_stockout_change_tv,
            lead_time_change_days=lead_time_tv,
            service_level_change=TrackedValue(value=None, state=ValueState.UNAVAILABLE, source="UNAVAILABLE"),
        )

        # Financial Impact Calculations (Zero-Fabrication - Rules 8 & 9)
        freight_cost_val = float(edge.cost.value) if (edge.cost and edge.cost.value is not None) else None

        if freight_cost_val is not None:
            transport_cost_tv = TrackedValue(
                value=round(freight_cost_val, 2),
                state=ValueState.OBSERVED,
                source="EDGE_FREIGHT_COST",
            )
        else:
            transport_cost_tv = TrackedValue(
                value=None,
                state=ValueState.UNAVAILABLE,
                source="MISSING_EDGE_FREIGHT_COST",
            )

        if unit_cost is not None and unit_cost >= 0.0:
            rebalanced_value = round(transfer_qty * unit_cost, 2)
            working_cap_tv = TrackedValue(
                value=rebalanced_value,
                state=ValueState.DERIVED,
                source="REBALANCED_INVENTORY_VALUE",
            )
        else:
            working_cap_tv = TrackedValue(
                value=None,
                state=ValueState.UNAVAILABLE,
                source="MISSING_UNIT_COST",
            )

        financial_impact = FinancialImpact(
            total_cost_change=transport_cost_tv,
            working_capital_released=working_cap_tv,
            transportation_cost_change=transport_cost_tv,
            currency=edge.currency,
        )

        # 6. Build Decision Recommendation & Result
        rec_id = f"REC-REBAL-{uuid.uuid4().hex[:8]}"

        dst_opt_state = OptimizedState(
            inventory_value=TrackedValue(
                value=round(new_dst_inv * unit_cost, 2) if unit_cost is not None else None,
                state=ValueState.DERIVED if unit_cost is not None else ValueState.UNAVAILABLE,
                source="POST_REBALANCE_INVENTORY_VALUE",
            ),
            coverage_days=TrackedValue(
                value=round(new_dst_cov, 2) if new_dst_cov != float('inf') else float('inf'),
                state=ValueState.DERIVED,
                source="POST_REBALANCE_COVERAGE",
            ),
            service_exposure_risk=TrackedValue(
                value=new_dst_risk,
                state=ValueState.DERIVED,
                source="POST_REBALANCE_RISK",
            ),
            bottleneck_active=dst_baseline.bottleneck_active,
        )

        cov_imp_str = f"{cov_improvement_days:.1f}d" if cov_improvement_days != float('inf') else "inf"
        justification = [
            f"Source {source_node.node_id} has {src_excess:.1f} units excess above {source_target_coverage_days:.1f}d target.",
            f"Destination {dest_node.node_id} has a shortage of {dst_shortage:.1f} units below {dest_target_coverage_days:.1f}d target.",
            f"Transferring {transfer_qty:.1f} units increases coverage by {cov_imp_str} and reduces risk by {risk_reduction * 100:.0f}%.",
        ]

        recommendation = DecisionRecommendation(
            recommendation_id=rec_id,
            decision_type=DecisionType.INVENTORY_REBALANCE,
            sku_id=edge.sku_id,
            source_node=source_node.node_id,
            destination_node=dest_node.node_id,
            quantity=transfer_qty,
            timing_days=lead_time_val,
            baseline=dst_baseline,
            optimized_state=dst_opt_state,
            operational_impact=operational_impact,
            financial_impact=financial_impact,
            justification=justification,
            constraints_evaluated=solver_logs,
            feasibility=feasibility,
            evidence_quality="HIGH" if edge.cost and edge.cost.state == ValueState.OBSERVED else "MEDIUM",
        )

        return OptimizationResult(
            status=OptimizationStatus.RECOMMENDED,
            reason=(
                f"Successfully generated feasible rebalancing recommendation of {transfer_qty:.1f} units "
                f"from {source_node.node_id} to {dest_node.node_id}."
            ),
            recommended_action=recommendation,
            alternatives=[],
            limitations=[],
        )