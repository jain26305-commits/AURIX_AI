"""Comprehensive Unit, Integration, Adversarial, and Configuration Test Suite for Phase 5."""

import unittest
from typing import Any, Dict
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Database & Model Imports
from aurix_core.database.engine import Base
from aurix_core.database.models import (
    forecasting,
    ingestion,
    inventory_intelligence,
    supply_chain,
    supply_intelligence,
)
from aurix_core.database.repositories.supply_intelligence import (
    ReplenishmentRecommendationRepository,
    SupplierPerformanceRepository,
    SupplyIntelligenceRunRepository,
)

# Contract & Schema Imports
from aurix_core.schema.phase5_contract import TrackedValue, ValueState
from aurix_core.schema.phase6_contract import (
    CapacityStatus,
    ReplenishmentUrgency,
    SupplyRiskLevel,
)

# Analytical Core & Service Imports
from aurix_core.supply.config import SupplyConfiguration
from aurix_core.supply.evaluator import SupplierCandidate, SupplierEvaluator
from aurix_core.supply.orchestrator import Phase5Orchestrator
from aurix_core.supply.performance import SupplierPerformanceCalculator
from aurix_core.supply.selection import SupplierSelector
from aurix_core.supply.service import SupplyIntelligenceService
import aurix_core.supply.orchestrator as supply_orch_module


class TestPhase5Supply(unittest.TestCase):

    def _create_mock_phase4_output(
        self,
        sku_id: str = "SKU-001",
        status: str = "COMPUTABLE",
        order_qty: float = 100.0,
        risk_status: str = "HIGH_RISK",
        coverage_days: float = 5.0,
    ) -> Dict[str, Any]:
        sku_contract = {
            "sku_id": sku_id,
            "status": status,
            "missing_inputs": [],
            "metrics": {
                "safety_stock": {
                    "value": 20.0,
                    "state": "DERIVED",
                    "source": "COMBINED_STD",
                },
                "reorder_point": {
                    "value": 50.0,
                    "state": "DERIVED",
                    "source": "DEMAND_LT_PLUS_SS",
                },
                "economic_order_quantity": {
                    "value": 100.0,
                    "state": "DERIVED",
                    "source": "EOQ",
                },
                "order_quantity": {
                    "value": order_qty,
                    "state": "DERIVED",
                    "source": "REORDER_POINT",
                },
                "inventory_position": {
                    "value": 30.0,
                    "state": "DERIVED",
                    "source": "POS",
                },
                "inventory_coverage_days": {
                    "value": coverage_days,
                    "state": "DERIVED",
                    "source": "COV",
                },
            },
            "risk_status": risk_status,
            "financials": {
                "inventory_value": {
                    "value": 500.0,
                    "state": "DERIVED",
                    "source": "COST",
                },
                "holding_cost_exposure": {
                    "value": 100.0,
                    "state": "DERIVED",
                    "source": "RATE",
                },
                "stockout_cost_exposure": {
                    "value": None,
                    "state": "UNAVAILABLE",
                    "source": "NONE",
                },
            },
            "policy_applied": "REORDER_POINT_CONTINUOUS_REVIEW",
            "limitations": [],
            "provenance": {
                "phase4_run_id": "RUN-P4-123",
                "dataset_hash": "a1b2c3d4e5f67890",
            },
        }

        return {
            "run_id": "RUN-P4-123",
            "timestamp": "2026-08-11T00:00:00",
            "portfolio_summary": {"total_skus": 1},
            "sku_inventory_intelligence": {sku_id: sku_contract},
        }

    # 1. Performance Calculator Tests
    def test_01_performance_empty_po_records(self) -> None:
        perf = SupplierPerformanceCalculator.calculate_performance([])
        self.assertEqual(perf.total_orders_evaluated, 0)
        self.assertEqual(perf.otif_rate.state, ValueState.UNAVAILABLE)

    def test_02_performance_valid_po_records(self) -> None:
        po_records = [
            {
                "order_date": "2026-01-01",
                "promised_date": "2026-01-08",
                "actual_delivery_date": "2026-01-07",
                "ordered_qty": 100.0,
                "received_qty": 100.0,
                "defective_qty": 0.0,
            },
            {
                "order_date": "2026-01-10",
                "promised_date": "2026-01-17",
                "actual_delivery_date": "2026-01-18",
                "ordered_qty": 200.0,
                "received_qty": 200.0,
                "defective_qty": 2.0,
            },
        ]
        perf = SupplierPerformanceCalculator.calculate_performance(po_records)
        self.assertEqual(perf.total_orders_evaluated, 2)
        self.assertEqual(perf.on_time_delivery_rate.value, 0.5)
        self.assertEqual(perf.in_full_delivery_rate.value, 1.0)
        self.assertEqual(perf.otif_rate.value, 0.5)
        self.assertEqual(perf.fill_rate.value, 1.0)
        self.assertIsNotNone(perf.mean_lead_time_days.value)
        self.assertIsNotNone(perf.lead_time_std_days.value)

    # 2. Evaluator Tests
    def test_03_evaluator_ineligible_supplier(self) -> None:
        candidate = SupplierCandidate(
            supplier_id="SUP-001",
            supplier_name="Bad Price Supplier",
            unit_price=TrackedValue(value=0.0, state=ValueState.OBSERVED, source="QUOTE"),
            lead_time_days=TrackedValue(value=7.0, state=ValueState.OBSERVED, source="QUOTE"),
        )
        eval_res = SupplierEvaluator.evaluate_supplier(candidate, required_quantity=100.0)
        self.assertFalse(eval_res.is_eligible)
        self.assertEqual(eval_res.selection_status, "REJECTED")

    def test_04_evaluator_moq_and_pack_size(self) -> None:
        candidate = SupplierCandidate(
            supplier_id="SUP-002",
            supplier_name="Constrained Supplier",
            unit_price=TrackedValue(value=10.0, state=ValueState.OBSERVED, source="QUOTE"),
            lead_time_days=TrackedValue(value=5.0, state=ValueState.OBSERVED, source="QUOTE"),
            moq=TrackedValue(value=200.0, state=ValueState.OBSERVED, source="QUOTE"),
            pack_size=TrackedValue(value=50.0, state=ValueState.OBSERVED, source="QUOTE"),
            capacity_units=TrackedValue(value=1000.0, state=ValueState.OBSERVED, source="QUOTE"),
        )
        eval_res = SupplierEvaluator.evaluate_supplier(candidate, required_quantity=120.0)
        self.assertTrue(eval_res.is_eligible)
        self.assertEqual(eval_res.constrained_order_quantity, 200.0)
        self.assertTrue(eval_res.moq_applied)
        self.assertEqual(eval_res.total_purchase_cost, 2000.0)

    # 3. Selector Tests
    def test_05_selector_multi_candidate_ranking(self) -> None:
        cand1 = SupplierCandidate(
            supplier_id="SUP-A",
            supplier_name="Cheap Expensive Risk",
            unit_price=TrackedValue(value=5.0, state=ValueState.OBSERVED, source="QUOTE"),
            lead_time_days=TrackedValue(value=10.0, state=ValueState.OBSERVED, source="QUOTE"),
            capacity_units=TrackedValue(value=50.0, state=ValueState.OBSERVED, source="QUOTE"),
        )
        cand2 = SupplierCandidate(
            supplier_id="SUP-B",
            supplier_name="Reliable Primary",
            unit_price=TrackedValue(value=6.0, state=ValueState.OBSERVED, source="QUOTE"),
            lead_time_days=TrackedValue(value=5.0, state=ValueState.OBSERVED, source="QUOTE"),
            capacity_units=TrackedValue(value=500.0, state=ValueState.OBSERVED, source="QUOTE"),
        )

        eval1 = SupplierEvaluator.evaluate_supplier(cand1, required_quantity=100.0)
        eval2 = SupplierEvaluator.evaluate_supplier(cand2, required_quantity=100.0)

        rec, ranked, summary = SupplierSelector.select_supplier([eval1, eval2])
        self.assertIsNotNone(rec)
        if rec:
            self.assertEqual(rec.supplier_id, "SUP-B")
            self.assertEqual(rec.selection_status, "RECOMMENDED")
        self.assertEqual(len(ranked), 2)
        self.assertFalse(summary.single_source_dependency)

    def test_06_selector_single_source_risk(self) -> None:
        cand = SupplierCandidate(
            supplier_id="SUP-SOLO",
            supplier_name="Sole Supplier",
            unit_price=TrackedValue(value=10.0, state=ValueState.OBSERVED, source="QUOTE"),
            lead_time_days=TrackedValue(value=5.0, state=ValueState.OBSERVED, source="QUOTE"),
        )
        eval_item = SupplierEvaluator.evaluate_supplier(cand, required_quantity=100.0)
        rec, ranked, summary = SupplierSelector.select_supplier([eval_item])
        self.assertTrue(summary.single_source_dependency)
        self.assertIn("SINGLE_SOURCE_DEPENDENCY", summary.primary_risk_drivers)

    # 4. Orchestrator Integration Tests
    def test_07_orchestrator_computable_sku(self) -> None:
        p4_output = self._create_mock_phase4_output("SKU-100", order_qty=150.0, risk_status="HIGH_RISK")
        supplier_data = {
            "SKU-100": [
                {
                    "supplier_id": "SUP-101",
                    "supplier_name": "Apex Supply Co",
                    "unit_price": 12.5,
                    "lead_time_days": 7,
                    "capacity_units": 1000,
                    "po_history": [
                        {
                            "order_date": "2026-02-01",
                            "promised_date": "2026-02-08",
                            "actual_delivery_date": "2026-02-07",
                            "ordered_qty": 100.0,
                            "received_qty": 100.0,
                        }
                    ],
                }
            ]
        }
        orch = Phase5Orchestrator(p4_output, supplier_data=supplier_data)
        res = orch.execute()

        self.assertEqual(res["portfolio_summary"]["computable_skus"], 1)
        sku_res = res["sku_supply_intelligence"]["SKU-100"]
        self.assertEqual(sku_res["status"], "COMPUTABLE")
        self.assertTrue(sku_res["replenishment"]["required"])
        self.assertEqual(sku_res["replenishment"]["urgency"], ReplenishmentUrgency.REPLENISH_NOW.value)
        self.assertIsNotNone(sku_res["recommended_supplier"])
        self.assertEqual(sku_res["recommended_supplier"]["supplier_id"], "SUP-101")

    def test_08_orchestrator_missing_supplier_data(self) -> None:
        p4_output = self._create_mock_phase4_output("SKU-200")
        orch = Phase5Orchestrator(p4_output, supplier_data={})
        res = orch.execute()

        self.assertEqual(res["portfolio_summary"]["input_required_skus"], 1)
        sku_res = res["sku_supply_intelligence"]["SKU-200"]
        self.assertEqual(sku_res["status"], "USER_INPUT_REQUIRED")
        self.assertEqual(sku_res["supply_risk"]["overall_risk_level"], SupplyRiskLevel.CRITICAL.value)

    def test_09_orchestrator_portfolio_summary(self) -> None:
        p4_output = self._create_mock_phase4_output("SKU-A", order_qty=50.0)
        p4_output["sku_inventory_intelligence"]["SKU-B"] = p4_output["sku_inventory_intelligence"]["SKU-A"].copy()
        p4_output["sku_inventory_intelligence"]["SKU-B"]["sku_id"] = "SKU-B"

        supplier_data = {
            "SKU-A": [
                {
                    "supplier_id": "SUP-1",
                    "supplier_name": "Supplier 1",
                    "unit_price": 10.0,
                    "lead_time_days": 5,
                }
            ]
        }
        orch = Phase5Orchestrator(p4_output, supplier_data=supplier_data)
        res = orch.execute()

        self.assertEqual(res["portfolio_summary"]["total_skus"], 2)
        self.assertEqual(res["portfolio_summary"]["computable_skus"], 1)
        self.assertEqual(res["portfolio_summary"]["input_required_skus"], 1)
        self.assertEqual(res["portfolio_summary"]["total_estimated_purchase_spend"], 500.0)

    # 5. Targeted Hardening & Adversarial Tests (10 - 19)
    def test_10_selection_low_risk_vs_high_risk_lower_price(self) -> None:
        cand_cheap_high_risk = SupplierCandidate(
            supplier_id="SUP-CHEAP-RISKY",
            supplier_name="Cheap Risky Supplier",
            unit_price=TrackedValue(value=10.0, state=ValueState.OBSERVED, source="QUOTE"),
            lead_time_days=TrackedValue(value=5.0, state=ValueState.OBSERVED, source="QUOTE"),
            capacity_units=TrackedValue(value=1000.0, state=ValueState.OBSERVED, source="QUOTE"),
        )
        cand_pricey_low_risk = SupplierCandidate(
            supplier_id="SUP-PRICEY-SAFE",
            supplier_name="Pricey Safe Supplier",
            unit_price=TrackedValue(value=12.0, state=ValueState.OBSERVED, source="QUOTE"),
            lead_time_days=TrackedValue(value=5.0, state=ValueState.OBSERVED, source="QUOTE"),
            capacity_units=TrackedValue(value=1000.0, state=ValueState.OBSERVED, source="QUOTE"),
        )

        eval_risky = SupplierEvaluator.evaluate_supplier(cand_cheap_high_risk, required_quantity=100.0)
        eval_safe = SupplierEvaluator.evaluate_supplier(cand_pricey_low_risk, required_quantity=100.0)

        eval_risky_high = eval_risky.model_copy(
            update={"supply_risk_level": SupplyRiskLevel.HIGH, "supply_risk_score": 0.65}
        )
        eval_safe_low = eval_safe.model_copy(
            update={"supply_risk_level": SupplyRiskLevel.LOW, "supply_risk_score": 0.10}
        )

        rec, _, _ = SupplierSelector.select_supplier([eval_risky_high, eval_safe_low])
        self.assertIsNotNone(rec)
        if rec:
            self.assertEqual(rec.supplier_id, "SUP-PRICEY-SAFE")

    def test_11_selection_capacity_sufficient_high_risk_vs_unknown_low_risk(self) -> None:
        eval_suff_high_risk = SupplierEvaluator.evaluate_supplier(
            SupplierCandidate(
                supplier_id="SUP-SUFF-HIGH",
                supplier_name="Sufficient High Risk",
                unit_price=TrackedValue(value=10.0, state=ValueState.OBSERVED, source="QUOTE"),
                lead_time_days=TrackedValue(value=5.0, state=ValueState.OBSERVED, source="QUOTE"),
                capacity_units=TrackedValue(value=1000.0, state=ValueState.OBSERVED, source="QUOTE"),
            ),
            required_quantity=100.0,
        ).model_copy(
            update={
                "supply_risk_level": SupplyRiskLevel.HIGH,
                "capacity_status": CapacityStatus.CAPACITY_SUFFICIENT,
            }
        )

        eval_unk_low_risk = SupplierEvaluator.evaluate_supplier(
            SupplierCandidate(
                supplier_id="SUP-UNK-LOW",
                supplier_name="Unknown Low Risk",
                unit_price=TrackedValue(value=10.0, state=ValueState.OBSERVED, source="QUOTE"),
                lead_time_days=TrackedValue(value=5.0, state=ValueState.OBSERVED, source="QUOTE"),
            ),
            required_quantity=100.0,
        ).model_copy(
            update={
                "supply_risk_level": SupplyRiskLevel.LOW,
                "capacity_status": CapacityStatus.CAPACITY_UNKNOWN,
            }
        )

        rec, _, _ = SupplierSelector.select_supplier([eval_suff_high_risk, eval_unk_low_risk])
        self.assertIsNotNone(rec)
        if rec:
            self.assertEqual(rec.supplier_id, "SUP-UNK-LOW")

    def test_12_selection_capacity_constrained_vs_reliable(self) -> None:
        eval_constrained = SupplierEvaluator.evaluate_supplier(
            SupplierCandidate(
                supplier_id="SUP-CONSTRAINED",
                supplier_name="Constrained Supplier",
                unit_price=TrackedValue(value=10.0, state=ValueState.OBSERVED, source="QUOTE"),
                lead_time_days=TrackedValue(value=5.0, state=ValueState.OBSERVED, source="QUOTE"),
                capacity_units=TrackedValue(value=50.0, state=ValueState.OBSERVED, source="QUOTE"),
            ),
            required_quantity=100.0,
        )

        eval_unconstrained = SupplierEvaluator.evaluate_supplier(
            SupplierCandidate(
                supplier_id="SUP-UNCONSTRAINED",
                supplier_name="Unconstrained Supplier",
                unit_price=TrackedValue(value=10.0, state=ValueState.OBSERVED, source="QUOTE"),
                lead_time_days=TrackedValue(value=5.0, state=ValueState.OBSERVED, source="QUOTE"),
                capacity_units=TrackedValue(value=500.0, state=ValueState.OBSERVED, source="QUOTE"),
            ),
            required_quantity=100.0,
        )

        rec, _, _ = SupplierSelector.select_supplier([eval_constrained, eval_unconstrained])
        self.assertIsNotNone(rec)
        if rec:
            self.assertEqual(rec.supplier_id, "SUP-UNCONSTRAINED")

    def test_13_selection_same_risk_same_capacity_different_cost(self) -> None:
        cand_cheap = SupplierCandidate(
            supplier_id="SUP-CHEAP",
            supplier_name="Cheap Supplier",
            unit_price=TrackedValue(value=8.0, state=ValueState.OBSERVED, source="QUOTE"),
            lead_time_days=TrackedValue(value=5.0, state=ValueState.OBSERVED, source="QUOTE"),
        )
        cand_expensive = SupplierCandidate(
            supplier_id="SUP-EXPENSIVE",
            supplier_name="Expensive Supplier",
            unit_price=TrackedValue(value=12.0, state=ValueState.OBSERVED, source="QUOTE"),
            lead_time_days=TrackedValue(value=5.0, state=ValueState.OBSERVED, source="QUOTE"),
        )

        eval1 = SupplierEvaluator.evaluate_supplier(cand_cheap, required_quantity=100.0)
        eval2 = SupplierEvaluator.evaluate_supplier(cand_expensive, required_quantity=100.0)

        rec, _, _ = SupplierSelector.select_supplier([eval1, eval2])
        self.assertIsNotNone(rec)
        if rec:
            self.assertEqual(rec.supplier_id, "SUP-CHEAP")

    def test_14_selection_same_cost_different_risk(self) -> None:
        eval_low_score = SupplierEvaluator.evaluate_supplier(
            SupplierCandidate(
                supplier_id="SUP-SCORE-LOW",
                supplier_name="Low Score Supplier",
                unit_price=TrackedValue(value=10.0, state=ValueState.OBSERVED, source="QUOTE"),
                lead_time_days=TrackedValue(value=5.0, state=ValueState.OBSERVED, source="QUOTE"),
            ),
            required_quantity=100.0,
        ).model_copy(update={"supply_risk_score": 0.10})

        eval_high_score = SupplierEvaluator.evaluate_supplier(
            SupplierCandidate(
                supplier_id="SUP-SCORE-HIGH",
                supplier_name="High Score Supplier",
                unit_price=TrackedValue(value=10.0, state=ValueState.OBSERVED, source="QUOTE"),
                lead_time_days=TrackedValue(value=5.0, state=ValueState.OBSERVED, source="QUOTE"),
            ),
            required_quantity=100.0,
        ).model_copy(update={"supply_risk_score": 0.20})

        rec, _, _ = SupplierSelector.select_supplier([eval_low_score, eval_high_score])
        self.assertIsNotNone(rec)
        if rec:
            self.assertEqual(rec.supplier_id, "SUP-SCORE-LOW")

    def test_15_selection_same_risk_cost_different_lead_time_reliability(self) -> None:
        cand_stable = SupplierCandidate(
            supplier_id="SUP-STABLE-LT",
            supplier_name="Stable Lead Time",
            unit_price=TrackedValue(value=10.0, state=ValueState.OBSERVED, source="QUOTE"),
            lead_time_days=TrackedValue(value=5.0, state=ValueState.OBSERVED, source="QUOTE"),
            lead_time_std_days=TrackedValue(value=0.5, state=ValueState.OBSERVED, source="QUOTE"),
        )
        cand_volatile = SupplierCandidate(
            supplier_id="SUP-VOLATILE-LT",
            supplier_name="Volatile Lead Time",
            unit_price=TrackedValue(value=10.0, state=ValueState.OBSERVED, source="QUOTE"),
            lead_time_days=TrackedValue(value=5.0, state=ValueState.OBSERVED, source="QUOTE"),
            lead_time_std_days=TrackedValue(value=3.0, state=ValueState.OBSERVED, source="QUOTE"),
        )

        eval_st = SupplierEvaluator.evaluate_supplier(cand_stable, required_quantity=100.0)
        eval_vol = SupplierEvaluator.evaluate_supplier(cand_volatile, required_quantity=100.0)

        rec, _, _ = SupplierSelector.select_supplier([eval_st, eval_vol])
        self.assertIsNotNone(rec)
        if rec:
            self.assertEqual(rec.supplier_id, "SUP-STABLE-LT")

    def test_16_selection_deterministic_identical_suppliers_tie_break(self) -> None:
        cand_z = SupplierCandidate(
            supplier_id="SUP-Z",
            supplier_name="Identical Z",
            unit_price=TrackedValue(value=10.0, state=ValueState.OBSERVED, source="QUOTE"),
            lead_time_days=TrackedValue(value=5.0, state=ValueState.OBSERVED, source="QUOTE"),
        )
        cand_a = SupplierCandidate(
            supplier_id="SUP-A",
            supplier_name="Identical A",
            unit_price=TrackedValue(value=10.0, state=ValueState.OBSERVED, source="QUOTE"),
            lead_time_days=TrackedValue(value=5.0, state=ValueState.OBSERVED, source="QUOTE"),
        )

        eval_z = SupplierEvaluator.evaluate_supplier(cand_z, required_quantity=100.0)
        eval_a = SupplierEvaluator.evaluate_supplier(cand_a, required_quantity=100.0)

        rec, _, _ = SupplierSelector.select_supplier([eval_z, eval_a])
        self.assertIsNotNone(rec)
        if rec:
            self.assertEqual(rec.supplier_id, "SUP-A")

    def test_17_selection_all_ineligible(self) -> None:
        cand_bad_price = SupplierCandidate(
            supplier_id="SUP-BAD",
            supplier_name="Bad Price",
            unit_price=TrackedValue(value=0.0, state=ValueState.OBSERVED, source="QUOTE"),
            lead_time_days=TrackedValue(value=5.0, state=ValueState.OBSERVED, source="QUOTE"),
        )
        eval_bad = SupplierEvaluator.evaluate_supplier(cand_bad_price, required_quantity=100.0)
        rec, _, summary = SupplierSelector.select_supplier([eval_bad])

        self.assertIsNone(rec)
        self.assertEqual(summary.overall_risk_level, SupplyRiskLevel.CRITICAL)
        self.assertIn("NO_ELIGIBLE_SUPPLIERS", summary.primary_risk_drivers)

    def test_18_risk_score_boundary_conditions(self) -> None:
        cfg = SupplyConfiguration()
        self.assertEqual(cfg.risk_low_max, 0.25)
        self.assertEqual(cfg.risk_moderate_max, 0.50)
        self.assertEqual(cfg.risk_high_max, 0.75)

        cand = SupplierCandidate(
            supplier_id="SUP-BND",
            supplier_name="Boundary Supplier",
            unit_price=TrackedValue(value=10.0, state=ValueState.OBSERVED, source="QUOTE"),
            lead_time_days=TrackedValue(value=5.0, state=ValueState.OBSERVED, source="QUOTE"),
        )

        eval_res = SupplierEvaluator.evaluate_supplier(cand, required_quantity=100.0, config=cfg)
        self.assertEqual(eval_res.supply_risk_score, 0.25)
        self.assertEqual(eval_res.supply_risk_level, SupplyRiskLevel.MODERATE)

    def test_19_configurable_risk_thresholds(self) -> None:
        custom_cfg = SupplyConfiguration({"otif_warning_threshold": 0.90, "otif_penalty": 0.30})
        cand = SupplierCandidate(
            supplier_id="SUP-CFG",
            supplier_name="Config Supplier",
            unit_price=TrackedValue(value=10.0, state=ValueState.OBSERVED, source="QUOTE"),
            lead_time_days=TrackedValue(value=5.0, state=ValueState.OBSERVED, source="QUOTE"),
            performance=SupplierPerformanceCalculator.calculate_performance(
                [
                    {
                        "order_date": "2026-01-01",
                        "promised_date": "2026-01-08",
                        "actual_delivery_date": "2026-01-07",
                        "ordered_qty": 100.0,
                        "received_qty": 100.0,
                    },
                    {
                        "order_date": "2026-01-10",
                        "promised_date": "2026-01-17",
                        "actual_delivery_date": "2026-01-20",
                        "ordered_qty": 100.0,
                        "received_qty": 100.0,
                    },
                ]
            ),
        )

        eval_default = SupplierEvaluator.evaluate_supplier(cand, required_quantity=100.0)
        eval_custom = SupplierEvaluator.evaluate_supplier(cand, required_quantity=100.0, config=custom_cfg)

        self.assertEqual(eval_default.supply_risk_score, 0.35)
        self.assertEqual(eval_custom.supply_risk_score, 0.40)


class TestPhase5SupplyPersistence(unittest.TestCase):
    """Enterprise integration tests verifying persistence, multi-tenant isolation, zero-fabrication, and rollback."""

    def setUp(self) -> None:
        self.engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})

        # Register modules with SQLAlchemy Base metadata
        _ = supply_intelligence.__name__
        _ = inventory_intelligence.__name__
        _ = forecasting.__name__
        _ = supply_chain.__name__
        _ = ingestion.__name__

        Base.metadata.create_all(bind=self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine, autocommit=False, autoflush=False)
        self.db: Session = self.SessionLocal()

        self.tenant_a = "tenant_alpha"
        self.tenant_b = "tenant_beta"

        self.mock_payload = {
            "sku_id": "SKU-SUPPLY-1",
            "required_qty": 500.0,
            "candidates": [{"supplier_id": "SUP-101", "unit_price": 15.0}],
        }
        self.mock_config = {"risk_weight": 0.3}

        # Inject Mock Supply Orchestrator to isolate service layer testing
        class MockSupplyOrchestrator:
            def __init__(self, payload: Any = None, config: Any = None, *args: Any, **kwargs: Any) -> None:
                pass

            def execute(self) -> Dict[str, Any]:
                return {
                    "supplier_performances": [
                        {
                            "supplier_id": "SUP-101",
                            "evaluated_order_count": 12,
                            "otd_rate": 0.95,
                            "in_full_rate": 0.90,
                            "otif_rate": 0.88,
                            "fill_rate": 0.96,
                            "lead_time_mean": 6.5,
                            "lead_time_std": 1.2,
                            "defect_rate": 0.01,
                            "risk_score": 0.12,
                            "risk_level": "LOW_RISK",
                            "risk_drivers": ["ACCEPTABLE_PERFORMANCE"],
                        }
                    ],
                    "replenishment_recommendations": [
                        {
                            "replenishment_policy_id": None,
                            "sku_id": "SKU-SUPPLY-1",
                            "supplier_id": "SUP-101",
                            "raw_quantity": 500.0,
                            "constrained_quantity": 600.0,
                            "moq_applied": True,
                            "pack_size_applied": False,
                            "unit_price": 15.0,
                            "total_purchase_cost": 9000.0,
                            "currency": "USD",
                            "selection_rank": 1,
                            "selection_reason": "LOWEST_RISK_ELIGIBLE",
                            "single_source_dependency": True,
                            "value_state": "COMPUTED",
                        }
                    ],
                    "provenance": {"engine": "Phase5MockEngine"},
                }

        self.original_orchestrator = getattr(supply_orch_module, "SupplyOrchestrator", None)
        self.original_phase5_orchestrator = getattr(supply_orch_module, "Phase5Orchestrator", None)

        setattr(supply_orch_module, "SupplyOrchestrator", MockSupplyOrchestrator)
        setattr(supply_orch_module, "Phase5Orchestrator", MockSupplyOrchestrator)

    def tearDown(self) -> None:
        if self.original_orchestrator:
            setattr(supply_orch_module, "SupplyOrchestrator", self.original_orchestrator)
        elif hasattr(supply_orch_module, "SupplyOrchestrator"):
            delattr(supply_orch_module, "SupplyOrchestrator")

        if self.original_phase5_orchestrator:
            setattr(supply_orch_module, "Phase5Orchestrator", self.original_phase5_orchestrator)
        elif hasattr(supply_orch_module, "Phase5Orchestrator"):
            delattr(supply_orch_module, "Phase5Orchestrator")

        self.db.close()
        Base.metadata.drop_all(bind=self.engine)

    def test_20_supply_persistence_and_provenance(self) -> None:
        """Verifies supply performances and recommendations are committed to the database."""
        service = SupplyIntelligenceService(self.db, self.tenant_a)
        res = service.run_supply_intelligence(self.mock_payload, config=self.mock_config)

        self.assertEqual(res["status"], "COMPLETED")
        self.assertFalse(res["idempotent_hit"])
        self.assertEqual(res["performance_count"], 1)
        self.assertEqual(res["recommendation_count"], 1)

        run_repo = SupplyIntelligenceRunRepository(self.db, self.tenant_a)
        run_rec = run_repo.get_by_id(res["supply_run_id"])
        self.assertIsNotNone(run_rec)

        perf_repo = SupplierPerformanceRepository(self.db, self.tenant_a)
        perfs = perf_repo.list_by_run_id(res["supply_run_id"])
        self.assertEqual(len(perfs), 1)
        self.assertEqual(perfs[0].supplier_id, "SUP-101")
        self.assertEqual(perfs[0].evaluated_order_count, 12)

        rec_repo = ReplenishmentRecommendationRepository(self.db, self.tenant_a)
        recs = rec_repo.list_by_run_id(res["supply_run_id"])
        self.assertEqual(len(recs), 1)
        self.assertEqual(recs[0].constrained_quantity, 600.0)
        self.assertTrue(recs[0].single_source_dependency)

    def test_21_supply_tenant_isolation(self) -> None:
        """Adversarial Test: Tenant B cannot query Tenant A's supply runs or recommendations."""
        service_a = SupplyIntelligenceService(self.db, self.tenant_a)
        res_a = service_a.run_supply_intelligence(self.mock_payload, config=self.mock_config)
        run_id_a = res_a["supply_run_id"]

        run_repo_b = SupplyIntelligenceRunRepository(self.db, self.tenant_b)
        perf_repo_b = SupplierPerformanceRepository(self.db, self.tenant_b)
        rec_repo_b = ReplenishmentRecommendationRepository(self.db, self.tenant_b)

        self.assertIsNone(run_repo_b.get_by_id(run_id_a))
        self.assertEqual(len(perf_repo_b.list_by_run_id(run_id_a)), 0)
        self.assertEqual(len(rec_repo_b.list_by_run_id(run_id_a)), 0)

    def test_22_supply_run_idempotency(self) -> None:
        """Verifies duplicate dataset payloads return cached run IDs without duplicating database rows."""
        service = SupplyIntelligenceService(self.db, self.tenant_a)

        res1 = service.run_supply_intelligence(self.mock_payload, config=self.mock_config)
        self.assertFalse(res1["idempotent_hit"])

        res2 = service.run_supply_intelligence(self.mock_payload, config=self.mock_config)
        self.assertTrue(res2["idempotent_hit"])
        self.assertEqual(res1["supply_run_id"], res2["supply_run_id"])

    def test_23_zero_fabrication_preservation(self) -> None:
        """Verifies uncomputed metrics and pricing remain NULL in the database."""
        class MockMissingPricingOrchestrator:
            def __init__(self, payload: Any = None, config: Any = None, *args: Any, **kwargs: Any) -> None:
                pass

            def execute(self) -> Dict[str, Any]:
                return {
                    "supplier_performances": [
                        {
                            "supplier_id": "SUP-NEW",
                            "evaluated_order_count": 0,
                            "otd_rate": None,
                            "otif_rate": None,
                        }
                    ],
                    "replenishment_recommendations": [
                        {
                            "sku_id": "SKU-NO-PRICE",
                            "supplier_id": "SUP-NEW",
                            "raw_quantity": 100.0,
                            "constrained_quantity": 100.0,
                            "unit_price": None,
                            "total_purchase_cost": None,
                            "currency": None,
                        }
                    ],
                }

        setattr(supply_orch_module, "SupplyOrchestrator", MockMissingPricingOrchestrator)
        setattr(supply_orch_module, "Phase5Orchestrator", MockMissingPricingOrchestrator)

        service = SupplyIntelligenceService(self.db, self.tenant_a)
        res = service.run_supply_intelligence(self.mock_payload, config=self.mock_config)

        perf_repo = SupplierPerformanceRepository(self.db, self.tenant_a)
        perfs = perf_repo.list_by_run_id(res["supply_run_id"])
        self.assertIsNone(perfs[0].otif_rate)
        self.assertNotEqual(perfs[0].otif_rate, 0.0)

        rec_repo = ReplenishmentRecommendationRepository(self.db, self.tenant_a)
        recs = rec_repo.list_by_run_id(res["supply_run_id"])
        self.assertIsNone(recs[0].unit_price)
        self.assertNotEqual(recs[0].unit_price, 0.0)

    def test_24_transaction_rollback_on_failure(self) -> None:
        """Verifies engine errors trigger atomic rollbacks and record a FAILED run status."""
        class FailingSupplyOrchestrator:
            def __init__(self, payload: Any = None, config: Any = None, *args: Any, **kwargs: Any) -> None:
                pass

            def execute(self) -> Dict[str, Any]:
                raise ValueError("Simulated invalid supplier constraint error")

        setattr(supply_orch_module, "SupplyOrchestrator", FailingSupplyOrchestrator)
        setattr(supply_orch_module, "Phase5Orchestrator", FailingSupplyOrchestrator)

        service = SupplyIntelligenceService(self.db, self.tenant_a)
        res = service.run_supply_intelligence(self.mock_payload, config=self.mock_config)

        self.assertEqual(res["status"], "FAILED")
        self.assertIn("Simulated invalid supplier constraint error", res["error"])

        run_repo = SupplyIntelligenceRunRepository(self.db, self.tenant_a)
        run_record = run_repo.get_by_id(res["supply_run_id"])
        self.assertIsNotNone(run_record)
        if run_record:
            self.assertEqual(run_record.status, "FAILED")