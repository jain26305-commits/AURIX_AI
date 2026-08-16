"""Comprehensive Unit, Integration, Adversarial, and Portfolio Test Suite for Phase 7B Decision Intelligence."""

import unittest
from typing import Any, Dict
from aurix_core.decision.baseline import BaselineEngine
from aurix_core.decision.config import DecisionConfiguration
from aurix_core.decision.gate import OptimizationGate
from aurix_core.decision.orchestrator import Phase7BOrchestrator
from aurix_core.decision.rebalancing import InventoryRebalancer
from aurix_core.decision.solver import ConstraintSatisfactionSolver
from aurix_core.decision.tradeoff import TradeoffEvaluator
from aurix_core.network.topology import NetworkTopologyBuilder
from aurix_core.schema.phase5_contract import ValueState
from aurix_core.schema.phase8_contract import NodeType
from aurix_core.schema.phase9_contract import (
    DecisionType,
    FeasibilityStatus,
    OptimizationStatus,
)


class TestPhase7BDecision(unittest.TestCase):
    """Unit and integration test cases for Phase 7B Decision & Optimization Intelligence."""

    def setUp(self) -> None:
        self.config = DecisionConfiguration()

    # 1. Baseline Engine Tests
    def test_01_baseline_evaluation_and_zero_demand(self) -> None:
        node = NetworkTopologyBuilder.build_node_identity(
            node_id="DC-01",
            node_type=NodeType.DISTRIBUTION_CENTER,
            inventory_units=500.0,
            demand_units=10.0,
            capacity_units=1000.0,
        )

        baseline = BaselineEngine.evaluate_node_baseline(
            node, unit_cost=15.0, target_coverage_days=20.0
        )
        self.assertEqual(baseline.inventory_value.value, 7500.0)
        self.assertEqual(baseline.coverage_days.value, 50.0)
        self.assertEqual(baseline.service_exposure_risk.value, 0.0)
        self.assertFalse(baseline.bottleneck_active)

        # Zero demand yields infinite coverage safely
        node_zero_demand = NetworkTopologyBuilder.build_node_identity(
            node_id="DC-02",
            node_type=NodeType.DISTRIBUTION_CENTER,
            inventory_units=100.0,
            demand_units=0.0,
        )
        base_zero = BaselineEngine.evaluate_node_baseline(
            node_zero_demand, unit_cost=10.0, target_coverage_days=20.0
        )
        self.assertEqual(base_zero.coverage_days.value, float("inf"))
        self.assertEqual(base_zero.service_exposure_risk.value, 0.0)

    # 2. Optimization Gate Readiness Tests
    def test_02_optimization_gate_validations(self) -> None:
        src = NetworkTopologyBuilder.build_node_identity(
            "DC-SRC", NodeType.DISTRIBUTION_CENTER, inventory_units=100.0
        )
        dst = NetworkTopologyBuilder.build_node_identity(
            "DC-DST", NodeType.DISTRIBUTION_CENTER, inventory_units=10.0
        )
        edge = NetworkTopologyBuilder.build_network_edge("DC-SRC", "DC-DST", "SKU-1", 50.0)

        # Valid readiness
        is_ready, status, _ = OptimizationGate.check_rebalancing_readiness(src, dst, edge)
        self.assertTrue(is_ready)
        self.assertEqual(status, OptimizationStatus.FEASIBLE)

        # Missing edge -> NOT_OPTIMIZABLE
        is_ready_no_edge, status_no_edge, _ = OptimizationGate.check_rebalancing_readiness(
            src, dst, edge=None
        )
        self.assertFalse(is_ready_no_edge)
        self.assertEqual(status_no_edge, OptimizationStatus.NOT_OPTIMIZABLE)

        # Identical nodes -> NOT_OPTIMIZABLE
        is_ready_same, status_same, _ = OptimizationGate.check_rebalancing_readiness(
            src, src, edge
        )
        self.assertFalse(is_ready_same)
        self.assertEqual(status_same, OptimizationStatus.NOT_OPTIMIZABLE)

    # 3. Constraint Satisfaction Solver Tests (Rule 7: Ceil-first & Fallbacks)
    def test_03_constraint_solver_pack_size_and_moq(self) -> None:
        qty, feasibility, logs = ConstraintSatisfactionSolver.solve_rebalancing_quantity(
            source_available_excess=100.0,
            destination_shortage=45.0,
            destination_available_capacity=50.0,
            pack_size=10.0,
            min_transfer_quantity=5.0,
        )
        self.assertEqual(qty, 50.0)
        self.assertEqual(feasibility, FeasibilityStatus.FEASIBLE)
        self.assertGreater(len(logs), 0)

        # MOQ Violation test (Qty 3 < MOQ 10 -> Cancelled)
        qty_moq, feasibility_moq, _ = ConstraintSatisfactionSolver.solve_rebalancing_quantity(
            source_available_excess=3.0,
            destination_shortage=3.0,
            pack_size=1.0,
            min_transfer_quantity=10.0,
        )
        self.assertEqual(qty_moq, 0.0)
        self.assertEqual(feasibility_moq, FeasibilityStatus.MOQ_VIOLATION)

    # 4. Inventory Rebalancing Domain Tests
    def test_04_inventory_rebalancer_execution_and_impact(self) -> None:
        src = NetworkTopologyBuilder.build_node_identity(
            "DC-EAST", NodeType.DISTRIBUTION_CENTER, inventory_units=1000.0, demand_units=10.0
        )
        dst = NetworkTopologyBuilder.build_node_identity(
            "DC-WEST", NodeType.DISTRIBUTION_CENTER, inventory_units=50.0, demand_units=10.0
        )
        edge = NetworkTopologyBuilder.build_network_edge(
            "DC-EAST", "DC-WEST", "SKU-A", 150.0, lead_time_days=3.0, cost=250.0
        )

        res = InventoryRebalancer.evaluate_rebalance(
            source_node=src,
            dest_node=dst,
            edge=edge,
            source_target_coverage_days=20.0,
            dest_target_coverage_days=20.0,
            unit_cost=12.0,
            pack_size=10.0,
            config=self.config,
        )

        self.assertEqual(res.status, OptimizationStatus.RECOMMENDED)
        self.assertIsNotNone(res.recommended_action)
        assert res.recommended_action is not None

        self.assertEqual(res.recommended_action.quantity, 150.0)
        self.assertEqual(res.recommended_action.decision_type, DecisionType.INVENTORY_REBALANCE)
        self.assertEqual(
            res.recommended_action.financial_impact.total_cost_change.value, 250.0
        )
        self.assertEqual(
            res.recommended_action.financial_impact.working_capital_released.value, 1800.0
        )

    # 5. Zero-Fabrication Financial Safeguard Tests
    def test_05_rebalance_missing_financial_data(self) -> None:
        src = NetworkTopologyBuilder.build_node_identity(
            "DC-EAST", NodeType.DISTRIBUTION_CENTER, inventory_units=500.0, demand_units=10.0
        )
        dst = NetworkTopologyBuilder.build_node_identity(
            "DC-WEST", NodeType.DISTRIBUTION_CENTER, inventory_units=50.0, demand_units=10.0
        )
        edge = NetworkTopologyBuilder.build_network_edge(
            "DC-EAST", "DC-WEST", "SKU-NO-COST", 100.0, cost=None
        )

        res = InventoryRebalancer.evaluate_rebalance(
            source_node=src,
            dest_node=dst,
            edge=edge,
            unit_cost=None,
            config=self.config,
        )

        self.assertEqual(res.status, OptimizationStatus.RECOMMENDED)
        assert res.recommended_action is not None
        self.assertEqual(
            res.recommended_action.financial_impact.total_cost_change.state,
            ValueState.UNAVAILABLE,
        )
        self.assertEqual(
            res.recommended_action.financial_impact.working_capital_released.state,
            ValueState.UNAVAILABLE,
        )

    # 6. Trade-off Evaluator Tests
    def test_06_tradeoff_comparison(self) -> None:
        src_a = NetworkTopologyBuilder.build_node_identity(
            "DC-A", NodeType.DISTRIBUTION_CENTER, inventory_units=500.0, demand_units=10.0
        )
        src_b = NetworkTopologyBuilder.build_node_identity(
            "DC-B", NodeType.DISTRIBUTION_CENTER, inventory_units=500.0, demand_units=10.0
        )
        dst = NetworkTopologyBuilder.build_node_identity(
            "DC-DEST", NodeType.DISTRIBUTION_CENTER, inventory_units=50.0, demand_units=10.0
        )

        edge_a = NetworkTopologyBuilder.build_network_edge("DC-A", "DC-DEST", "SKU-A", 100.0, cost=300.0)
        edge_b = NetworkTopologyBuilder.build_network_edge("DC-B", "DC-DEST", "SKU-A", 100.0, cost=150.0)

        res_a = InventoryRebalancer.evaluate_rebalance(src_a, dst, edge_a, unit_cost=10.0)
        res_b = InventoryRebalancer.evaluate_rebalance(src_b, dst, edge_b, unit_cost=10.0)

        assert res_a.recommended_action is not None and res_b.recommended_action is not None

        tradeoffs = TradeoffEvaluator.compare_recommendations(
            res_a.recommended_action, [res_b.recommended_action]
        )
        self.assertEqual(len(tradeoffs), 1)
        self.assertIn("Lower transportation/transfer cost", tradeoffs[0].tradeoff_reason)

    # 7. End-to-End Orchestrator Portfolio Decision Tests
    def test_07_orchestrator_end_to_end_decisions(self) -> None:
        p7a_output: Dict[str, Any] = {
            "status": "COMPUTABLE",
            "nodes": {
                "DC-100": {
                    "node_id": "DC-100",
                    "node_type": "DISTRIBUTION_CENTER",
                    "node_name": "East Hub",
                    "capacity": {"value": 1000.0, "state": "OBSERVED", "source": "NODE_RECORD"},
                    "inventory": {"value": 800.0, "state": "DERIVED", "source": "PHASE4_INVENTORY"},
                    "demand": {"value": 10.0, "state": "DERIVED", "source": "PHASE2_DEMAND"},
                    "service_level": {"value": 0.95, "state": "OBSERVED", "source": "PERFORMANCE"},
                    "value_state": "OBSERVED",
                },
                "DC-200": {
                    "node_id": "DC-200",
                    "node_type": "DISTRIBUTION_CENTER",
                    "node_name": "West Hub",
                    "capacity": {"value": 1000.0, "state": "OBSERVED", "source": "NODE_RECORD"},
                    "inventory": {"value": 50.0, "state": "DERIVED", "source": "PHASE4_INVENTORY"},
                    "demand": {"value": 10.0, "state": "DERIVED", "source": "PHASE2_DEMAND"},
                    "service_level": {"value": 0.90, "state": "OBSERVED", "source": "PERFORMANCE"},
                    "value_state": "OBSERVED",
                },
            },
            "edges": [
                {
                    "source_node_id": "DC-100",
                    "destination_node_id": "DC-200",
                    "sku_id": "SKU-PORT",
                    "flow_quantity": {"value": 150.0, "state": "OBSERVED", "source": "FLOW_RECORD"},
                    "lead_time_days": {"value": 2.0, "state": "OBSERVED", "source": "TRANSIT"},
                    "cost": {"value": 120.0, "state": "OBSERVED", "source": "FREIGHT"},
                    "currency": "USD",
                }
            ],
            "inventory_imbalances": [
                {
                    "sku_id": "SKU-PORT",
                    "nodes_compared": ["DC-100", "DC-200"],
                    "coverage_days_by_node": {"DC-100": 80.0, "DC-200": 5.0},
                    "imbalance_detected": True,
                    "description": "Coverage ratio disparity detected.",
                }
            ],
            "node_flow_metrics": {},
            "vulnerabilities": {
                "single_source_dependencies": [],
                "single_node_dependencies": [],
                "high_flow_bottlenecks": [],
                "risk_indicators": [],
            },
            "bullwhip_metrics": [],
            "portfolio_summary": {
                "total_nodes": 2,
                "total_edges": 1,
                "total_skus_mapped": 1,
                "critical_vulnerabilities_count": 0,
                "bullwhip_amplifications_count": 0,
            },
            "limitations": [],
            "provenance": {"phase7a_run_id": "RUN-P7A-001"},
        }

        unit_costs = {"SKU-PORT": 20.0}

        orch = Phase7BOrchestrator(
            phase7a_network_output=p7a_output, unit_cost_by_sku=unit_costs
        )
        res = orch.execute()

        self.assertEqual(res["status"], "COMPUTABLE")
        self.assertIn("SKU-PORT", res["decisions"])
        sku_decision = res["decisions"]["SKU-PORT"]
        self.assertEqual(sku_decision["status"], OptimizationStatus.RECOMMENDED.value)
        self.assertIsNotNone(sku_decision["recommended_action"])
        self.assertEqual(sku_decision["recommended_action"]["source_node"], "DC-100")
        self.assertEqual(sku_decision["recommended_action"]["destination_node"], "DC-200")
        self.assertEqual(
            res["portfolio_financial_impact"]["total_cost_change"]["value"], 120.0
        )

    def test_08_orchestrator_missing_p7a_input(self) -> None:
        orch = Phase7BOrchestrator(phase7a_network_output={})
        res = orch.execute()

        self.assertEqual(res["status"], "USER_INPUT_REQUIRED")
        self.assertEqual(len(res["missing_inputs"]), 1)
        self.assertEqual(res["missing_inputs"][0]["field"], "phase7a_network_output")


if __name__ == "__main__":
    unittest.main()