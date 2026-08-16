"""Comprehensive Unit, Integration, Adversarial, and Persistence Test Suite for Phase 8 Economics."""

import unittest
from typing import Any, Dict
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Database & Engine Imports
from aurix_core.database.engine import Base
from aurix_core.database.models import (
    forecasting,
    ingestion,
    inventory_intelligence,
    logistics_intelligence,
    network_intelligence,
    supply_chain,
    supply_intelligence,
    economics as economics_models,
)
from aurix_core.database.repositories.economics import (
    FinancialBaselineSnapshotRepository,
    FinancialIntelligenceRunRepository,
)

# Economics Core & Service Imports
from aurix_core.economics.config import EconomicsConfiguration
from aurix_core.economics.financials import FinancialEngine
from aurix_core.economics.orchestrator import Phase8Orchestrator
from aurix_core.economics.service import FinancialIntelligenceService
from aurix_core.economics.simulator import ScenarioEngine
from aurix_core.schema.phase5_contract import TrackedValue, ValueState
from aurix_core.schema.phase10_contract import (
    ScenarioOverride,
    ScenarioStatus,
    ScenarioType,
)


class TestPhase8Economics(unittest.TestCase):
    """Unit and analytical domain test cases for Phase 8 Economics."""

    def setUp(self) -> None:
        self.config = EconomicsConfiguration()

    # 1. Working Capital & Holding Cost Tests
    def test_01_working_capital_calculation_normal(self) -> None:
        wc = FinancialEngine.calculate_working_capital(
            sku_id="SKU-01",
            node_id="DC-01",
            on_hand_units=1000.0,
            cycle_stock_units=600.0,
            safety_stock_units=400.0,
            excess_units=0.0,
            unit_cost=25.0,
            currency="USD",
            config=self.config,
        )

        self.assertEqual(wc.currency, "USD")
        self.assertEqual(wc.total_inventory_value.value, 25000.0)
        self.assertEqual(wc.cycle_stock_value.value, 15000.0)
        self.assertEqual(wc.safety_stock_value.value, 10000.0)
        self.assertEqual(wc.annual_holding_cost.value, 3750.0)
        self.assertEqual(wc.financial_risk_level.value, "MODERATE")

    def test_02_working_capital_missing_cost_zero_fabrication(self) -> None:
        wc = FinancialEngine.calculate_working_capital(
            sku_id="SKU-02",
            node_id="DC-02",
            on_hand_units=500.0,
            unit_cost=None,
            currency="USD",
            config=self.config,
        )

        self.assertEqual(wc.total_inventory_value.state, ValueState.UNAVAILABLE)
        self.assertIsNone(wc.total_inventory_value.value)
        self.assertEqual(wc.annual_holding_cost.state, ValueState.UNAVAILABLE)
        self.assertEqual(wc.financial_risk_level.value, "UNAVAILABLE")

    # 2. Total Cost of Ownership (TCO) Tests
    def test_03_tco_transparent_summation(self) -> None:
        p_cost = TrackedValue(value=10000.0, state=ValueState.DERIVED, source="PURCHASE")
        f_cost = TrackedValue(value=1200.0, state=ValueState.OBSERVED, source="FREIGHT")
        h_cost = TrackedValue(value=1500.0, state=ValueState.DERIVED, source="HOLDING")

        tco = FinancialEngine.calculate_tco(
            purchase_cost=p_cost,
            freight_cost=f_cost,
            holding_cost=h_cost,
            currency="USD",
        )

        self.assertEqual(tco.currency, "USD")
        self.assertEqual(tco.total_cost_of_ownership.value, 12700.0)
        self.assertEqual(tco.total_cost_of_ownership.state, ValueState.DERIVED)

    # 3. Currency-Isolated Portfolio Aggregation Tests
    def test_04_currency_isolated_portfolio_aggregation(self) -> None:
        wc_usd = FinancialEngine.calculate_working_capital(
            sku_id="SKU-USD", node_id="DC-1", on_hand_units=100.0, unit_cost=50.0, currency="USD"
        )
        wc_inr = FinancialEngine.calculate_working_capital(
            sku_id="SKU-INR", node_id="DC-2", on_hand_units=100.0, unit_cost=1000.0, currency="INR"
        )

        freight_records = [
            {"currency": "USD", "amount": 300.0},
            {"currency": "INR", "amount": 5000.0},
        ]

        portfolio = FinancialEngine.aggregate_portfolio_by_currency(
            exposures=[wc_usd, wc_inr], freight_records=freight_records
        )

        self.assertIn("USD", portfolio)
        self.assertIn("INR", portfolio)
        self.assertEqual(portfolio["USD"].total_inventory_value.value, 5000.0)
        self.assertEqual(portfolio["USD"].total_freight_spend.value, 300.0)
        self.assertEqual(portfolio["INR"].total_inventory_value.value, 100000.0)
        self.assertEqual(portfolio["INR"].total_freight_spend.value, 5000.0)

    # 4. Scenario Simulation Tests (Demand Shock & Isolation)
    def test_05_scenario_simulation_demand_shock(self) -> None:
        base_inv = {"USD": 20000.0}
        base_hold = {"USD": 3000.0}
        base_tco = {"USD": 25000.0}

        overrides = ScenarioOverride(demand_multiplier=1.15)
        res = ScenarioEngine.simulate_scenario(
            scenario_id="SCEN-TEST",
            scenario_type=ScenarioType.DEMAND_SHOCK,
            description="Test demand shock simulation (+15%)",
            overrides=overrides,
            baseline_inventory_value_by_currency=base_inv,
            baseline_holding_cost_by_currency=base_hold,
            baseline_tco_by_currency=base_tco,
            config=self.config,
        )

        self.assertEqual(res.status, ScenarioStatus.COMPUTED)
        self.assertIn("USD", res.financial_comparison_by_currency)
        comp = res.financial_comparison_by_currency["USD"]
        self.assertEqual(comp.baseline_inventory_value.value, 20000.0)
        self.assertEqual(comp.scenario_inventory_value.value, 23000.0)
        self.assertEqual(comp.inventory_value_delta.value, 3000.0)
        self.assertEqual(comp.scenario_tco.value, 28750.0)

    def test_06_scenario_infeasible_negative_multiplier(self) -> None:
        overrides = ScenarioOverride(demand_multiplier=-0.5)
        res = ScenarioEngine.simulate_scenario(
            scenario_id="SCEN-BAD",
            scenario_type=ScenarioType.DEMAND_SHOCK,
            description="Infeasible negative multiplier",
            overrides=overrides,
            baseline_inventory_value_by_currency={"USD": 10000.0},
        )
        self.assertEqual(res.status, ScenarioStatus.INFEASIBLE)
        self.assertGreater(len(res.limitations), 0)

    # 5. End-to-End Orchestrator Integration Tests
    def test_07_orchestrator_end_to_end_economics(self) -> None:
        p9_output: Dict[str, Any] = {
            "status": "COMPUTABLE",
            "portfolio_financial_impact": {
                "total_cost_change": {"value": 250.0, "state": "OBSERVED", "source": "FREIGHT"},
                "working_capital_released": {"value": 5000.0, "state": "DERIVED", "source": "REBALANCE"},
                "transportation_cost_change": {"value": 250.0, "state": "OBSERVED", "source": "FREIGHT"},
                "currency": "USD",
            },
            "decisions": {
                "SKU-TEST-01": {
                    "status": "RECOMMENDED",
                    "reason": "Feasible rebalance.",
                    "recommended_action": {
                        "recommendation_id": "REC-01",
                        "decision_type": "INVENTORY_REBALANCE",
                        "sku_id": "SKU-TEST-01",
                        "source_node": "DC-SRC",
                        "destination_node": "DC-DST",
                        "quantity": 200.0,
                        "baseline": {
                            "inventory_value": {"value": 15000.0, "state": "DERIVED", "source": "BASE"},
                            "coverage_days": {"value": 5.0, "state": "DERIVED", "source": "BASE"},
                            "service_exposure_risk": {"value": 0.5, "state": "DERIVED", "source": "BASE"},
                            "bottleneck_active": False,
                        },
                        "optimized_state": {
                            "inventory_value": {"value": 20000.0, "state": "DERIVED", "source": "OPT"},
                            "coverage_days": {"value": 20.0, "state": "DERIVED", "source": "OPT"},
                            "service_exposure_risk": {"value": 0.0, "state": "DERIVED", "source": "OPT"},
                            "bottleneck_active": False,
                        },
                        "operational_impact": {
                            "inventory_coverage_change_days": {"value": 15.0, "state": "DERIVED", "source": "DELTA"},
                            "stockout_exposure_change": {"value": -0.5, "state": "DERIVED", "source": "DELTA"},
                            "lead_time_change_days": {"value": 2.0, "state": "OBSERVED", "source": "LEAD"},
                            "service_level_change": {"value": None, "state": "UNAVAILABLE", "source": "UNAVAILABLE"},
                        },
                        "financial_impact": {
                            "total_cost_change": {"value": 250.0, "state": "OBSERVED", "source": "FREIGHT"},
                            "working_capital_released": {"value": 5000.0, "state": "DERIVED", "source": "WC"},
                            "transportation_cost_change": {"value": 250.0, "state": "OBSERVED", "source": "FREIGHT"},
                            "currency": "USD",
                        },
                        "feasibility": "FEASIBLE",
                        "evidence_quality": "HIGH",
                        "timing_days": 2.0,
                        "justification": ["Rebalance test."],
                        "constraints_evaluated": ["Capacity OK."],
                    },
                    "alternatives": [],
                    "limitations": [],
                }
            },
            "missing_inputs": [],
            "limitations": [],
            "provenance": {"phase7b_run_id": "RUN-P7B-001"},
        }

        orch = Phase8Orchestrator(phase7b_decision_output=p9_output)
        res = orch.execute()

        self.assertEqual(res["status"], "COMPUTABLE")
        self.assertIn("USD", res["portfolio_financials_by_currency"])
        self.assertIn("SKU-TEST-01", res["sku_working_capital"])
        self.assertIn("SKU-TEST-01", res["sku_tco"])
        self.assertIn("SCEN-DEMAND-UP", res["scenarios"])
        self.assertIn("SCEN-FREIGHT-UP", res["scenarios"])
        self.assertEqual(res["scenarios"]["SCEN-DEMAND-UP"]["status"], "COMPUTED")

    def test_08_orchestrator_missing_p7b_input(self) -> None:
        orch = Phase8Orchestrator(phase7b_decision_output={})
        res = orch.execute()

        self.assertEqual(res["status"], "USER_INPUT_REQUIRED")
        self.assertEqual(len(res["missing_inputs"]), 1)
        self.assertEqual(res["missing_inputs"][0]["field"], "phase7b_decision_output")


class TestPhase8EconomicsPersistence(unittest.TestCase):
    """Enterprise integration tests verifying database persistence, tenant isolation, and idempotency."""

    def setUp(self) -> None:
        self.engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})

        # Register all metadata
        _ = supply_chain.__name__
        _ = ingestion.__name__
        _ = forecasting.__name__
        _ = inventory_intelligence.__name__
        _ = supply_intelligence.__name__
        _ = logistics_intelligence.__name__
        _ = network_intelligence.__name__
        _ = economics_models.__name__

        Base.metadata.create_all(bind=self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine, autocommit=False, autoflush=False)
        self.db: Session = self.SessionLocal()

        self.tenant_a = "tenant_alpha"
        self.tenant_b = "tenant_beta"

        self.mock_payload: Dict[str, Any] = {
            "status": "COMPUTABLE",
            "portfolio_financial_impact": {
                "total_cost_change": {"value": 100.0, "state": "OBSERVED", "source": "FREIGHT"},
                "working_capital_released": {"value": 1000.0, "state": "DERIVED", "source": "WC"},
                "transportation_cost_change": {"value": 100.0, "state": "OBSERVED", "source": "FREIGHT"},
                "currency": "USD",
            },
            "decisions": {
                "SKU-TEST-01": {
                    "status": "RECOMMENDED",
                    "reason": "Feasible rebalance.",
                    "recommended_action": {
                        "recommendation_id": "REC-01",
                        "decision_type": "INVENTORY_REBALANCE",
                        "sku_id": "SKU-TEST-01",
                        "source_node": "DC-SRC",
                        "destination_node": "DC-DST",
                        "quantity": 200.0,
                        "baseline": {
                            "inventory_value": {"value": 15000.0, "state": "DERIVED", "source": "BASE"},
                            "coverage_days": {"value": 5.0, "state": "DERIVED", "source": "BASE"},
                            "service_exposure_risk": {"value": 0.5, "state": "DERIVED", "source": "BASE"},
                            "bottleneck_active": False,
                        },
                        "optimized_state": {
                            "inventory_value": {"value": 20000.0, "state": "DERIVED", "source": "OPT"},
                            "coverage_days": {"value": 20.0, "state": "DERIVED", "source": "OPT"},
                            "service_exposure_risk": {"value": 0.0, "state": "DERIVED", "source": "OPT"},
                            "bottleneck_active": False,
                        },
                        "operational_impact": {
                            "inventory_coverage_change_days": {"value": 15.0, "state": "DERIVED", "source": "DELTA"},
                            "stockout_exposure_change": {"value": -0.5, "state": "DERIVED", "source": "DELTA"},
                            "lead_time_change_days": {"value": 2.0, "state": "OBSERVED", "source": "LEAD"},
                            "service_level_change": {"value": None, "state": "UNAVAILABLE", "source": "UNAVAILABLE"},
                        },
                        "financial_impact": {
                            "total_cost_change": {"value": 100.0, "state": "OBSERVED", "source": "FREIGHT"},
                            "working_capital_released": {"value": 1000.0, "state": "DERIVED", "source": "WC"},
                            "transportation_cost_change": {"value": 100.0, "state": "OBSERVED", "source": "FREIGHT"},
                            "currency": "USD",
                        },
                        "feasibility": "FEASIBLE",
                        "evidence_quality": "HIGH",
                        "timing_days": 2.0,
                        "justification": ["Rebalance test."],
                        "constraints_evaluated": ["Capacity OK."],
                    },
                    "alternatives": [],
                    "limitations": [],
                }
            },
            "missing_inputs": [],
            "limitations": [],
            "provenance": {"phase7b_run_id": "RUN-P7B-001"},
        }
        self.mock_config: Dict[str, Any] = {"holding_cost_rate": 0.15}

    def tearDown(self) -> None:
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)

    def test_09_financial_persistence_and_provenance(self) -> None:
        """Verifies financial runs, baselines, and scenarios are committed to the database."""
        service = FinancialIntelligenceService(self.db, self.tenant_a)
        res = service.run_financial_intelligence(self.mock_payload, config=self.mock_config)

        self.assertEqual(res.get("status"), "COMPLETED")
        self.assertFalse(res.get("idempotent_hit"))

        run_repo = FinancialIntelligenceRunRepository(self.db, self.tenant_a)
        run_rec = run_repo.get_by_id(str(res.get("financial_run_id")))
        self.assertIsNotNone(run_rec)

        baseline_repo = FinancialBaselineSnapshotRepository(self.db, self.tenant_a)
        baselines = baseline_repo.list_by_run_id(str(res.get("financial_run_id")))
        self.assertEqual(len(baselines), 1)

    def test_10_financial_tenant_isolation(self) -> None:
        """Adversarial Test: Tenant B cannot query Tenant A's financial runs or snapshots."""
        service_a = FinancialIntelligenceService(self.db, self.tenant_a)
        res_a = service_a.run_financial_intelligence(self.mock_payload, config=self.mock_config)
        run_id_a = str(res_a.get("financial_run_id"))

        run_repo_b = FinancialIntelligenceRunRepository(self.db, self.tenant_b)
        baseline_repo_b = FinancialBaselineSnapshotRepository(self.db, self.tenant_b)

        self.assertIsNone(run_repo_b.get_by_id(run_id_a))
        self.assertEqual(len(baseline_repo_b.list_by_run_id(run_id_a)), 0)

    def test_11_financial_run_idempotency(self) -> None:
        """Verifies duplicate payloads return cached run IDs without duplicating database rows."""
        service = FinancialIntelligenceService(self.db, self.tenant_a)

        res1 = service.run_financial_intelligence(self.mock_payload, config=self.mock_config)
        self.assertFalse(res1.get("idempotent_hit"))

        res2 = service.run_financial_intelligence(self.mock_payload, config=self.mock_config)
        self.assertTrue(res2.get("idempotent_hit"))
        self.assertEqual(res1.get("financial_run_id"), res2.get("financial_run_id"))


if __name__ == "__main__":
    unittest.main()