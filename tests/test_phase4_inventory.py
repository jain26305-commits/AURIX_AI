"""Comprehensive Unit, Integration, Adversarial, and Persistence Test Suite for Phase 4 Inventory."""

import unittest
from typing import Any, Dict, List, Optional
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from aurix_core.inventory.config import InventoryConfiguration
from aurix_core.inventory.gate import InventoryReadinessGate
from aurix_core.inventory.mathematics import InventoryMathematics
from aurix_core.inventory.orchestrator import Phase4Orchestrator
from aurix_core.inventory.risk import InventoryRiskEvaluator

# Enterprise Persistence & Service Imports
from aurix_core.database.engine import Base
from aurix_core.database.models import inventory_intelligence, forecasting, supply_chain, ingestion
from aurix_core.database.repositories.inventory_intelligence import (
    InventoryIntelligenceRunRepository,
    ReplenishmentPolicyRepository,
)
from aurix_core.inventory.service import InventoryIntelligenceService
import aurix_core.inventory.orchestrator as inv_orch_module


class TestPhase4Inventory(unittest.TestCase):
    """Original analytical and mathematical test suite for Inventory Intelligence."""

    def _create_mock_phase3_output(
        self,
        sku_id: str = "SKU-001",
        forecast_vals: Optional[List[float]] = None,
        rmse: float = 2.0,
    ) -> Dict[str, Any]:
        if forecast_vals is None:
            forecast_vals = [10.0, 12.0, 11.0, 13.0]

        fc_points = [
            {
                "date": f"2026-08-{i+1:02d}",
                "point_forecast": val,
                "raw_model_forecast": val,
                "constraint_applied": False,
                "constraint_reason": None,
                "lower_bound": val - 2.0,
                "upper_bound": val + 2.0,
                "interval_status": "COMPUTED",
            }
            for i, val in enumerate(forecast_vals)
        ]

        sku_contract = {
            "entity_id": sku_id,
            "forecast_status": "FORECAST_AVAILABLE",
            "champion_model": "XGBOOST",
            "forecast_horizon": len(forecast_vals),
            "forecast": fc_points,
            "selection_reason": "Top performer",
            "baseline_model": "NAIVE",
            "model_competition": [
                {
                    "model_id": "XGBOOST",
                    "status": "EVALUATED",
                    "reason": "OK",
                    "folds_tested": 2,
                    "wape": 0.05,
                    "mae": 1.5,
                    "rmse": rmse,
                    "bias": 0.0,
                    "stability_variance": 0.001,
                    "baseline_improvement_pct": 0.10,
                }
            ],
            "data_quality_flags": [],
            "limitations": [],
            "provenance": {
                "phase3_run_id": "RUN-P3-123",
                "dataset_hash": "a1b2c3d4e5f67890",
            },
        }

        return {
            "run_id": "RUN-P3-123",
            "timestamp": "2026-08-11T00:00:00",
            "portfolio_summary": {"total_skus": 1},
            "sku_forecasts": {sku_id: sku_contract},
        }

    def test_01_combined_std_zero_lead_time_var(self) -> None:
        std = InventoryMathematics.calculate_combined_std(
            daily_demand_mean=10.0, daily_demand_std=2.0, lead_time_days=9.0, lead_time_std=0.0
        )
        self.assertEqual(std, 6.0)

    def test_02_combined_std_with_lead_time_var(self) -> None:
        std = InventoryMathematics.calculate_combined_std(
            daily_demand_mean=10.0, daily_demand_std=2.0, lead_time_days=9.0, lead_time_std=1.0
        )
        self.assertAlmostEqual(std, 11.66, places=1)

    def test_03_safety_stock_and_rop(self) -> None:
        ss = InventoryMathematics.calculate_safety_stock(z_score=1.645, combined_std=10.0)
        self.assertEqual(ss, 16.45)
        rop = InventoryMathematics.calculate_reorder_point(daily_demand_mean=10.0, lead_time_days=7.0, safety_stock=ss)
        self.assertEqual(rop, 86.45)

    def test_04_eoq_normal(self) -> None:
        eoq = InventoryMathematics.calculate_eoq(
            annual_demand=3650.0, ordering_cost=50.0, holding_cost_per_unit_year=4.0
        )
        self.assertIsNotNone(eoq)
        if eoq is not None:
            self.assertAlmostEqual(eoq, 302.08, places=1)

    def test_05_eoq_zero_division_protection(self) -> None:
        eoq = InventoryMathematics.calculate_eoq(annual_demand=100.0, ordering_cost=0.0, holding_cost_per_unit_year=0.0)
        self.assertIsNone(eoq)

    def test_06_moq_and_pack_size_constraints(self) -> None:
        qty, applied, reason = InventoryMathematics.apply_order_constraints(
            raw_quantity=45.0, moq=100.0, pack_size=20.0
        )
        self.assertEqual(qty, 100.0)
        self.assertTrue(applied)
        self.assertIsNotNone(reason)
        if reason:
            self.assertIn("MOQ_APPLIED", reason)

        qty2, applied2, reason2 = InventoryMathematics.apply_order_constraints(
            raw_quantity=105.0, moq=50.0, pack_size=20.0
        )
        self.assertEqual(qty2, 120.0)
        self.assertTrue(applied2)
        self.assertIsNotNone(reason2)
        if reason2:
            self.assertIn("PACK_SIZE_MULTIPLE", reason2)

    def test_07_inventory_position_and_coverage(self) -> None:
        pos = InventoryMathematics.calculate_inventory_position(on_hand=100.0, inbound=50.0, committed=20.0)
        self.assertEqual(pos, 130.0)
        cov = InventoryMathematics.calculate_coverage_days(inventory_qty=100.0, daily_demand_mean=10.0)
        self.assertEqual(cov, 10.0)

    def test_08_readiness_gate_missing_lead_time(self) -> None:
        is_computable, missing = InventoryReadinessGate.evaluate({"expected_daily_demand": 10.0})
        self.assertFalse(is_computable)
        self.assertTrue(any(m["field"] == "lead_time_days" for m in missing))

    def test_09_z_score_config_mapping(self) -> None:
        self.assertEqual(InventoryConfiguration.get_z_score(0.95), 1.645)
        self.assertEqual(InventoryConfiguration.get_z_score(0.99), 2.326)

    def test_10_stockout_imminent_risk(self) -> None:
        risk = InventoryRiskEvaluator.evaluate_risk(
            on_hand_qty=20.0,
            inventory_position=20.0,
            reorder_point=50.0,
            safety_stock=10.0,
            lead_time_days=7.0,
            daily_demand=10.0,
        )
        self.assertEqual(risk["stockout_risk"], "STOCKOUT_IMMINENT")

    def test_11_excess_inventory_risk(self) -> None:
        risk = InventoryRiskEvaluator.evaluate_risk(
            on_hand_qty=1000.0,
            inventory_position=1000.0,
            reorder_point=100.0,
            safety_stock=20.0,
            lead_time_days=7.0,
            daily_demand=10.0,
        )
        self.assertEqual(risk["excess_status"], "EXCESS_INVENTORY")

    def test_12_orchestrator_computable_sku(self) -> None:
        p3_output = self._create_mock_phase3_output("SKU-100", [10.0, 10.0, 10.0, 10.0], rmse=2.0)
        user_inputs = {
            "SKU-100": {
                "lead_time_days": 7,
                "unit_cost": 25.0,
                "on_hand_qty": 50.0,
            }
        }
        orch = Phase4Orchestrator(p3_output, user_inputs=user_inputs)
        res = orch.execute()

        self.assertEqual(res["portfolio_summary"]["computable_skus"], 1)
        sku_res = res["sku_inventory_intelligence"]["SKU-100"]
        self.assertEqual(sku_res["status"], "COMPUTABLE")
        self.assertIsNotNone(sku_res["metrics"]["safety_stock"]["value"])
        self.assertIsNotNone(sku_res["financials"]["inventory_value"]["value"])

    def test_13_orchestrator_missing_input_sku(self) -> None:
        p3_output = self._create_mock_phase3_output("SKU-200")
        orch = Phase4Orchestrator(p3_output, user_inputs={})
        res = orch.execute()

        self.assertEqual(res["portfolio_summary"]["input_required_skus"], 1)
        sku_res = res["sku_inventory_intelligence"]["SKU-200"]
        self.assertEqual(sku_res["status"], "USER_INPUT_REQUIRED")
        self.assertEqual(sku_res["risk_status"], "NOT_ASSESSABLE")

    def test_14_portfolio_mixed_skus(self) -> None:
        p3_output = self._create_mock_phase3_output("SKU-A", [10.0, 10.0])
        p3_output["sku_forecasts"]["SKU-B"] = p3_output["sku_forecasts"]["SKU-A"].copy()
        p3_output["sku_forecasts"]["SKU-B"]["entity_id"] = "SKU-B"

        user_inputs = {"SKU-A": {"lead_time_days": 5, "unit_cost": 10.0}}

        orch = Phase4Orchestrator(p3_output, user_inputs=user_inputs)
        res = orch.execute()

        self.assertEqual(res["portfolio_summary"]["total_skus"], 2)
        self.assertEqual(res["portfolio_summary"]["computable_skus"], 1)
        self.assertEqual(res["portfolio_summary"]["input_required_skus"], 1)


class TestPhase4InventoryPersistence(unittest.TestCase):
    """Enterprise integration tests verifying multi-tenancy, persistence, and zero-fabrication rules."""

    def setUp(self) -> None:
        self.engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})

        # Ensure modules are loaded for SQLAlchemy metadata registration
        _ = inventory_intelligence.__name__
        _ = forecasting.__name__
        _ = supply_chain.__name__
        _ = ingestion.__name__

        Base.metadata.create_all(bind=self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine, autocommit=False, autoflush=False)
        self.db: Session = self.SessionLocal()

        self.tenant_a = "tenant_alpha"
        self.tenant_b = "tenant_beta"

        self.mock_input = {"forecast_data": "dummy"}
        self.mock_config = {"lead_time": 7}

        # Inject Mock Orchestrator to purely isolate testing to the Database/Service layer
        class MockInventoryOrchestrator:
            def __init__(self, portfolio_data: Any, config: Any) -> None:
                pass
            def execute(self) -> Dict[str, Any]:
                return {
                    "replenishment_policies": [
                        {
                            "sku_id": "SKU-TEST-1",
                            "expected_daily_demand": 10.0,
                            "lead_time_days": 5.0,
                            "safety_stock": 12.5,
                            "reorder_point": 62.5,
                            "eoq": 200.0,
                            "reorder_triggered": True,
                            "reorder_reason": "BELOW_ROP",
                            "raw_order_quantity": 250.0,
                            "constrained_order_quantity": 300.0,
                            "constraint_applied": True,
                            "constraint_reason": "PACK_SIZE",
                            "risk_status": "STOCKOUT_IMMINENT",
                            "holding_cost_exposure": 500.0
                        }
                    ],
                    "provenance": {"engine": "mocked"}
                }

        self.original_orchestrator = getattr(inv_orch_module, "InventoryOrchestrator", None)
        setattr(inv_orch_module, "InventoryOrchestrator", MockInventoryOrchestrator)

    def tearDown(self) -> None:
        if self.original_orchestrator:
            setattr(inv_orch_module, "InventoryOrchestrator", self.original_orchestrator)
        elif hasattr(inv_orch_module, "InventoryOrchestrator"):
            delattr(inv_orch_module, "InventoryOrchestrator")

        self.db.close()
        Base.metadata.drop_all(bind=self.engine)

    def test_15_inventory_persistence_and_provenance(self) -> None:
        """Verifies calculated policies are correctly committed to the canonical database."""
        service = InventoryIntelligenceService(self.db, self.tenant_a)
        res = service.run_inventory_intelligence(self.mock_input, config=self.mock_config)

        self.assertEqual(res["status"], "COMPLETED")
        self.assertFalse(res["idempotent_hit"])

        run_repo = InventoryIntelligenceRunRepository(self.db, self.tenant_a)
        run_record = run_repo.get_by_id(res["inventory_run_id"])
        self.assertIsNotNone(run_record)

        policy_repo = ReplenishmentPolicyRepository(self.db, self.tenant_a)
        policies = policy_repo.list_by_run_id(res["inventory_run_id"])
        self.assertEqual(len(policies), 1)
        self.assertEqual(policies[0].sku_id, "SKU-TEST-1")
        self.assertTrue(policies[0].constraint_applied)
        self.assertEqual(policies[0].constrained_order_quantity, 300.0)

    def test_16_inventory_tenant_isolation(self) -> None:
        """Adversarial Test: Tenant B must not be able to query Tenant A's inventory intelligence."""
        service_a = InventoryIntelligenceService(self.db, self.tenant_a)
        res_a = service_a.run_inventory_intelligence(self.mock_input, config=self.mock_config)
        run_id_a = res_a["inventory_run_id"]

        run_repo_b = InventoryIntelligenceRunRepository(self.db, self.tenant_b)
        policy_repo_b = ReplenishmentPolicyRepository(self.db, self.tenant_b)

        self.assertIsNone(run_repo_b.get_by_id(run_id_a))
        self.assertEqual(len(policy_repo_b.list_by_run_id(run_id_a)), 0)

    def test_17_inventory_run_idempotency(self) -> None:
        """Verifies duplicate dataset payloads return the cached Run ID without duplicating rows."""
        service = InventoryIntelligenceService(self.db, self.tenant_a)

        res1 = service.run_inventory_intelligence(self.mock_input, config=self.mock_config)
        self.assertFalse(res1["idempotent_hit"])

        res2 = service.run_inventory_intelligence(self.mock_input, config=self.mock_config)
        self.assertTrue(res2["idempotent_hit"])
        self.assertEqual(res1["inventory_run_id"], res2["inventory_run_id"])

    def test_18_zero_fabrication_preservation(self) -> None:
        """Verifies missing financial inputs correctly propagate as NULL to the DB, not 0.0."""
        class MockMissingFinancialsOrchestrator:
            def __init__(self, portfolio_data: Any, config: Any) -> None:
                pass
            def execute(self) -> Dict[str, Any]:
                return {
                    "replenishment_policies": [{"sku_id": "SKU-NO-COST", "holding_cost_exposure": None}]
                }

        setattr(inv_orch_module, "InventoryOrchestrator", MockMissingFinancialsOrchestrator)

        service = InventoryIntelligenceService(self.db, self.tenant_a)
        res = service.run_inventory_intelligence(self.mock_input, config=self.mock_config)

        policy_repo = ReplenishmentPolicyRepository(self.db, self.tenant_a)
        policies = policy_repo.list_by_run_id(res["inventory_run_id"])

        self.assertIsNone(policies[0].holding_cost_exposure)
        self.assertNotEqual(policies[0].holding_cost_exposure, 0.0)

    def test_19_transaction_rollback_on_failure(self) -> None:
        """Verifies engine errors rollback incomplete persistence and log a FAILED status."""
        class FailingOrchestrator:
            def __init__(self, portfolio_data: Any, config: Any) -> None:
                pass
            def execute(self) -> Dict[str, Any]:
                raise ZeroDivisionError("Simulated EOQ zero division error")

        setattr(inv_orch_module, "InventoryOrchestrator", FailingOrchestrator)

        service = InventoryIntelligenceService(self.db, self.tenant_a)
        res = service.run_inventory_intelligence(self.mock_input, config=self.mock_config)

        self.assertEqual(res["status"], "FAILED")
        self.assertIn("Simulated EOQ zero division error", res["error"])

        run_repo = InventoryIntelligenceRunRepository(self.db, self.tenant_a)
        run_record = run_repo.get_by_id(res["inventory_run_id"])
        self.assertIsNotNone(run_record)
        if run_record:
            self.assertEqual(run_record.status, "FAILED")
