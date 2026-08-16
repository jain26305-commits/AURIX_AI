"""Comprehensive Hardened Unit, Integration, Adversarial, and Persistence Test Suite for Phase 6."""

import unittest
from datetime import datetime, timedelta
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
    supply_chain,
    supply_intelligence,
)
from aurix_core.database.repositories.logistics_intelligence import (
    CarrierPerformanceRepository,
    LogisticsIntelligenceRunRepository,
    ShipmentEvaluationRepository,
)

# Logistics Intelligence Core & Service Imports
from aurix_core.logistics.config import LogisticsConfiguration
from aurix_core.logistics.eta_engine import DeterministicETAEngine
from aurix_core.logistics.orchestrator import Phase6Orchestrator
from aurix_core.logistics.performance import LogisticsPerformanceCalculator
from aurix_core.logistics.risk_consequence import (
    FreightEconomicsCalculator,
    InventoryConsequenceEngine,
    LogisticsRiskEvaluator,
)
from aurix_core.logistics.service import LogisticsIntelligenceService
from aurix_core.schema.phase5_contract import ValueState
from aurix_core.schema.phase6_contract import ReplenishmentUrgency, SupplyRiskLevel
import aurix_core.logistics.service as logistics_service_module


class TestPhase6Logistics(unittest.TestCase):
    """Unit and analytical domain test cases for Phase 6 Logistics Intelligence."""

    def _create_mock_phase5_output(
        self,
        sku_id: str = "SKU-LOG-01",
        status: str = "COMPUTABLE",
        urgency: ReplenishmentUrgency = ReplenishmentUrgency.REPLENISH_NOW,
        coverage_days: float = 3.0,
    ) -> Dict[str, Any]:
        sku_contract = {
            "sku_id": sku_id,
            "status": status,
            "missing_inputs": [],
            "replenishment": {
                "required": True,
                "base_required_quantity": 200.0,
                "urgency": urgency.value,
                "inventory_coverage_days": coverage_days,
                "reorder_point": 100.0,
                "inventory_position": 50.0,
                "reason": "Test replenishment requirement",
            },
            "recommended_supplier": {
                "supplier_id": "SUP-LOG-100",
                "supplier_name": "Apex Logistics Supplier",
                "is_eligible": True,
                "rejection_reason": None,
                "unit_price": 15.0,
                "currency": "USD",
                "raw_order_quantity": 200.0,
                "constrained_order_quantity": 200.0,
                "moq_applied": False,
                "pack_size_applied": False,
                "total_purchase_cost": 3000.0,
                "capacity_status": "CAPACITY_SUFFICIENT",
                "supply_risk_level": "LOW",
                "supply_risk_score": 0.10,
                "rank": 1,
                "selection_status": "RECOMMENDED",
                "preference_reasons": ["LOW_RISK"],
            },
            "candidate_evaluations": [],
            "supply_risk": {
                "overall_risk_level": "LOW",
                "single_source_dependency": False,
                "primary_risk_drivers": ["LOW_SUPPLY_CHAIN_FRICTION"],
            },
            "limitations": [],
            "provenance": {
                "phase5_run_id": "RUN-P5-123",
                "phase4_run_id": "RUN-P4-123",
                "dataset_hash": "abc123hash",
                "engine_version": "5.0.0",
            },
        }

        return {
            "run_id": "RUN-P5-123",
            "timestamp": "2026-08-11T00:00:00",
            "portfolio_summary": {"total_skus": 1},
            "sku_supply_intelligence": {sku_id: sku_contract},
        }

    # 1. Performance Calculator & Sample Size Tests
    def test_01_performance_empty_records(self) -> None:
        perf = LogisticsPerformanceCalculator.calculate_performance([])
        self.assertEqual(perf.get("sample_size"), 0)
        median_obj = perf.get("median_transit_days")
        self.assertIsNotNone(median_obj)
        if isinstance(median_obj, dict):
            unavail_str = (
                ValueState.UNAVAILABLE.value
                if hasattr(ValueState.UNAVAILABLE, "value")
                else str(ValueState.UNAVAILABLE)
            )
            self.assertEqual(median_obj.get("state"), unavail_str)

    def test_02_performance_sample_size_gates(self) -> None:
        # N = 2 (< min_sample_size = 3) -> Percentiles must be UNAVAILABLE
        records = [
            {
                "dispatch_date": "2026-01-01",
                "promised_delivery_date": "2026-01-05",
                "actual_delivery_date": "2026-01-05",
            },
            {
                "dispatch_date": "2026-01-10",
                "promised_delivery_date": "2026-01-15",
                "actual_delivery_date": "2026-01-14",
            },
        ]
        perf = LogisticsPerformanceCalculator.calculate_performance(records, min_sample_size=3)
        self.assertEqual(perf.get("sample_size"), 2)
        median_obj = perf.get("median_transit_days")
        self.assertIsNotNone(median_obj)
        if isinstance(median_obj, dict):
            unavail_str = (
                ValueState.UNAVAILABLE.value
                if hasattr(ValueState.UNAVAILABLE, "value")
                else str(ValueState.UNAVAILABLE)
            )
            self.assertEqual(median_obj.get("state"), unavail_str)
            self.assertEqual(median_obj.get("source"), "INSUFFICIENT_SAMPLE_SIZE")

        # N = 3 (>= min_sample_size = 3) -> Percentiles must be DERIVED
        records.append(
            {
                "dispatch_date": "2026-01-20",
                "promised_delivery_date": "2026-01-25",
                "actual_delivery_date": "2026-01-24",
            }
        )
        perf_n3 = LogisticsPerformanceCalculator.calculate_performance(records, min_sample_size=3)
        self.assertEqual(perf_n3.get("sample_size"), 3)
        median_obj_n3 = perf_n3.get("median_transit_days")
        self.assertIsNotNone(median_obj_n3)
        if isinstance(median_obj_n3, dict):
            derived_str = (
                ValueState.DERIVED.value
                if hasattr(ValueState.DERIVED, "value")
                else str(ValueState.DERIVED)
            )
            self.assertEqual(median_obj_n3.get("state"), derived_str)

    # 2. Strict Zero-Fabrication ETA Tests
    def test_03_zero_transit_evidence_returns_unavailable(self) -> None:
        shipment = {
            "shipment_id": "SHIP-NO-EVIDENCE",
            "sku_id": "SKU-LOG-01",
            "quantity": 100.0,
            "freight_cost": 500.0,
        }
        eta_res = DeterministicETAEngine.calculate_eta(shipment)
        self.assertIsNone(eta_res.get("estimated_delivery_date"))
        unavail_str = (
            ValueState.UNAVAILABLE.value
            if hasattr(ValueState.UNAVAILABLE, "value")
            else str(ValueState.UNAVAILABLE)
        )
        self.assertEqual(eta_res.get("value_state"), unavail_str)
        self.assertEqual(eta_res.get("eta_method"), "UNAVAILABLE")

    def test_04_tracker_active_in_transit_eta(self) -> None:
        now = datetime.now()
        dispatch_dt = now - timedelta(days=2)
        promised_dt = now + timedelta(days=5)

        shipment: Dict[str, Any] = {
            "shipment_id": "SHIP-001",
            "sku_id": "SKU-LOG-01",
            "dispatch_date": dispatch_dt.strftime("%Y-%m-%d"),
            "promised_delivery_date": promised_dt.strftime("%Y-%m-%d"),
            "planned_transit_days": 6.0,
            "quantity": 100.0,
            "freight_cost": 500.0,
            "currency": "USD",
        }
        carrier_perf: Dict[str, Any] = {"median_transit_days": 5.0, "sample_size": 10}
        eta_res = DeterministicETAEngine.calculate_eta(shipment, carrier_performance=carrier_perf)

        f_cost = float(shipment["freight_cost"]) if shipment.get("freight_cost") is not None else None
        qty = float(shipment["quantity"]) if shipment.get("quantity") is not None else None
        curr = str(shipment["currency"]) if shipment.get("currency") is not None else None

        cost_res = FreightEconomicsCalculator.calculate_freight_economics(
            freight_cost=f_cost,
            quantity=qty,
            weight_kg=None,
            currency=curr,
        )

        self.assertEqual(eta_res.get("eta_source"), "HISTORICAL_CARRIER_MEDIAN")
        self.assertIsNotNone(cost_res.get("cost_per_unit"))
        self.assertEqual(cost_res.get("cost_per_unit"), 5.0)

    # 3. Cost Division Safety & Zero/Negative Handling
    def test_05_cost_division_safety(self) -> None:
        cost_res = FreightEconomicsCalculator.calculate_freight_economics(
            freight_cost=-200.0,
            quantity=0.0,
            weight_kg=-10.0,
            currency="USD",
        )
        self.assertIsNone(cost_res.get("freight_cost"))
        self.assertIsNone(cost_res.get("cost_per_unit"))
        self.assertIsNone(cost_res.get("cost_per_kg"))
        unavail_str = (
            ValueState.UNAVAILABLE.value
            if hasattr(ValueState.UNAVAILABLE, "value")
            else str(ValueState.UNAVAILABLE)
        )
        self.assertEqual(cost_res.get("value_state"), unavail_str)

    # 4. Risk Boundaries & Expedite Decision Tests
    def test_06_risk_boundaries_and_clamping(self) -> None:
        cfg = LogisticsConfiguration()

        # Low risk test (0.10 base + 0.0 penalties)
        risk_low = LogisticsRiskEvaluator.evaluate_risk(
            delay_days=0.0,
            carrier_otd_rate=0.95,
            transit_std_days=1.0,
            inventory_coverage_days=30.0,
            config=cfg,
        )
        self.assertEqual(risk_low.get("risk_level"), SupplyRiskLevel.LOW)
        self.assertGreaterEqual(risk_low.get("risk_score", 0.0), 0.0)
        self.assertLessEqual(risk_low.get("risk_score", 1.0), 1.0)

        # Critical risk test (Coverage exhaustion + delay)
        risk_crit = LogisticsRiskEvaluator.evaluate_risk(
            delay_days=5.0,
            carrier_otd_rate=0.60,
            transit_std_days=4.0,
            inventory_coverage_days=2.0,
            config=cfg,
        )
        self.assertEqual(risk_crit.get("risk_level"), SupplyRiskLevel.CRITICAL)
        self.assertGreaterEqual(risk_crit.get("risk_score", 0.0), 0.0)
        self.assertLessEqual(risk_crit.get("risk_score", 1.0), 1.0)

    def test_07_inventory_consequence_variations(self) -> None:
        # Case A: Healthy inventory buffer
        expedite_a = InventoryConsequenceEngine.evaluate_expedite_decision(
            delay_days=3.0,
            inventory_coverage_days=25.0,
        )

        # Case B: Critical inventory buffer (Delay > Coverage)
        expedite_b = InventoryConsequenceEngine.evaluate_expedite_decision(
            delay_days=5.0,
            inventory_coverage_days=2.0,
        )

        self.assertEqual(expedite_a.get("expedite_recommendation"), "NORMAL_TRANSPORT")
        self.assertEqual(expedite_b.get("expedite_recommendation"), "EXPEDITE_CRITICAL")

    # 5. Orchestrator Integration Tests
    def test_08_orchestrator_e2e_computable(self) -> None:
        payload: Dict[str, Any] = {
            "shipments": [
                {
                    "shipment_id": "SHIP-100",
                    "sku_id": "SKU-LOG-01",
                    "carrier_id": "CARRIER-FAST",
                    "origin_id": "WH-ORIGIN",
                    "destination_id": "DC-DEST",
                    "dispatch_date": "2026-08-01",
                    "promised_delivery_date": "2026-08-07",
                    "quantity": 200.0,
                    "freight_cost": 1000.0,
                    "currency": "USD",
                }
            ],
            "carrier_history": {
                "CARRIER-FAST": [
                    {
                        "dispatch_date": "2026-01-01",
                        "promised_delivery_date": "2026-01-06",
                        "actual_delivery_date": "2026-01-06",
                    },
                    {
                        "dispatch_date": "2026-01-10",
                        "promised_delivery_date": "2026-01-15",
                        "actual_delivery_date": "2026-01-15",
                    },
                    {
                        "dispatch_date": "2026-01-20",
                        "promised_delivery_date": "2026-01-25",
                        "actual_delivery_date": "2026-01-25",
                    },
                ]
            },
            "inventory_coverage": {"SKU-LOG-01": 10.0},
        }

        orch = Phase6Orchestrator(payload)
        res = orch.execute()

        self.assertEqual(len(res.get("carrier_performances", [])), 1)
        self.assertEqual(len(res.get("shipment_evaluations", [])), 1)
        ship_eval = res["shipment_evaluations"][0]
        self.assertEqual(ship_eval.get("shipment_id"), "SHIP-100")
        self.assertEqual(ship_eval.get("expedite_recommendation"), "NORMAL_TRANSPORT")

    def test_09_orchestrator_missing_shipment_data(self) -> None:
        payload: Dict[str, Any] = {"shipments": [], "carrier_history": {}}
        orch = Phase6Orchestrator(payload)
        res = orch.execute()

        self.assertEqual(len(res.get("shipment_evaluations", [])), 0)
        self.assertEqual(res.get("provenance", {}).get("evaluated_shipments"), 0)


class TestPhase6LogisticsPersistence(unittest.TestCase):
    """Enterprise integration tests verifying DB persistence, tenant isolation, zero-fabrication, and rollback."""

    def setUp(self) -> None:
        self.engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})

        # Register modules with SQLAlchemy Base metadata
        _ = supply_chain.__name__
        _ = ingestion.__name__
        _ = forecasting.__name__
        _ = inventory_intelligence.__name__
        _ = supply_intelligence.__name__
        _ = logistics_intelligence.__name__

        Base.metadata.create_all(bind=self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine, autocommit=False, autoflush=False)
        self.db: Session = self.SessionLocal()

        self.tenant_a = "tenant_alpha"
        self.tenant_b = "tenant_beta"

        self.mock_payload: Dict[str, Any] = {
            "shipments": [
                {
                    "shipment_id": "SHIP-PERST-1",
                    "sku_id": "SKU-P6-1",
                    "carrier_id": "CARRIER-P6",
                    "quantity": 500.0,
                    "freight_cost": 2500.0,
                    "currency": "USD",
                }
            ],
            "carrier_history": {
                "CARRIER-P6": [
                    {
                        "dispatch_date": "2026-01-01",
                        "promised_delivery_date": "2026-01-05",
                        "actual_delivery_date": "2026-01-05",
                    },
                    {
                        "dispatch_date": "2026-01-10",
                        "promised_delivery_date": "2026-01-15",
                        "actual_delivery_date": "2026-01-15",
                    },
                    {
                        "dispatch_date": "2026-01-20",
                        "promised_delivery_date": "2026-01-25",
                        "actual_delivery_date": "2026-01-25",
                    },
                ]
            },
        }
        self.mock_config: Dict[str, Any] = {"min_sample_size": 3}

    def tearDown(self) -> None:
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)

    def test_10_logistics_persistence_and_provenance(self) -> None:
        """Verifies carrier performances and shipment evaluations are committed to the database."""
        service = LogisticsIntelligenceService(self.db, self.tenant_a)
        res = service.run_logistics_intelligence(self.mock_payload, config=self.mock_config)

        self.assertEqual(res.get("status"), "COMPLETED")
        self.assertFalse(res.get("idempotent_hit"))
        self.assertEqual(res.get("carrier_count"), 1)
        self.assertEqual(res.get("shipment_count"), 1)

        run_repo = LogisticsIntelligenceRunRepository(self.db, self.tenant_a)
        run_rec = run_repo.get_by_id(str(res.get("logistics_run_id")))
        self.assertIsNotNone(run_rec)

        carrier_repo = CarrierPerformanceRepository(self.db, self.tenant_a)
        carriers = carrier_repo.list_by_run_id(str(res.get("logistics_run_id")))
        self.assertEqual(len(carriers), 1)
        self.assertEqual(getattr(carriers[0], "carrier_id"), "CARRIER-P6")

        ship_repo = ShipmentEvaluationRepository(self.db, self.tenant_a)
        shipments = ship_repo.list_by_run_id(str(res.get("logistics_run_id")))
        self.assertEqual(len(shipments), 1)
        self.assertEqual(getattr(shipments[0], "cost_per_unit"), 5.0)

    def test_11_logistics_tenant_isolation(self) -> None:
        """Adversarial Test: Tenant B cannot query Tenant A's logistics runs or evaluations."""
        service_a = LogisticsIntelligenceService(self.db, self.tenant_a)
        res_a = service_a.run_logistics_intelligence(self.mock_payload, config=self.mock_config)
        run_id_a = str(res_a.get("logistics_run_id"))

        run_repo_b = LogisticsIntelligenceRunRepository(self.db, self.tenant_b)
        carrier_repo_b = CarrierPerformanceRepository(self.db, self.tenant_b)
        ship_repo_b = ShipmentEvaluationRepository(self.db, self.tenant_b)

        self.assertIsNone(run_repo_b.get_by_id(run_id_a))
        self.assertEqual(len(carrier_repo_b.list_by_run_id(run_id_a)), 0)
        self.assertEqual(len(ship_repo_b.list_by_run_id(run_id_a)), 0)

    def test_12_logistics_run_idempotency(self) -> None:
        """Verifies duplicate payloads return cached run IDs without duplicating database rows."""
        service = LogisticsIntelligenceService(self.db, self.tenant_a)

        res1 = service.run_logistics_intelligence(self.mock_payload, config=self.mock_config)
        self.assertFalse(res1.get("idempotent_hit"))

        res2 = service.run_logistics_intelligence(self.mock_payload, config=self.mock_config)
        self.assertTrue(res2.get("idempotent_hit"))
        self.assertEqual(res1.get("logistics_run_id"), res2.get("logistics_run_id"))

    def test_13_zero_fabrication_preservation(self) -> None:
        """Verifies uncomputed transit metrics and freight costs remain NULL in the database."""
        missing_payload: Dict[str, Any] = {
            "shipments": [
                {
                    "shipment_id": "SHIP-NO-COST",
                    "sku_id": "SKU-NO-COST",
                    "freight_cost": None,
                    "quantity": None,
                }
            ],
            "carrier_history": {},
        }
        service = LogisticsIntelligenceService(self.db, self.tenant_a)
        res = service.run_logistics_intelligence(missing_payload, config=self.mock_config)

        ship_repo = ShipmentEvaluationRepository(self.db, self.tenant_a)
        shipments = ship_repo.list_by_run_id(str(res.get("logistics_run_id")))
        self.assertIsNone(getattr(shipments[0], "cost_per_unit"))
        self.assertNotEqual(getattr(shipments[0], "cost_per_unit"), 0.0)

    def test_14_transaction_rollback_on_failure(self) -> None:
        """Verifies engine errors trigger atomic rollbacks and record a FAILED run status."""
        class FailingLogisticsOrchestrator:
            def __init__(self, payload: Any = None, config: Any = None, *args: Any, **kwargs: Any) -> None:
                pass

            def execute(self) -> Dict[str, Any]:
                raise ValueError("Simulated invalid logistics constraint error")

        original_orch = getattr(logistics_service_module, "Phase6Orchestrator", None)
        setattr(logistics_service_module, "Phase6Orchestrator", FailingLogisticsOrchestrator)

        try:
            service = LogisticsIntelligenceService(self.db, self.tenant_a)
            res = service.run_logistics_intelligence(self.mock_payload, config=self.mock_config)

            self.assertEqual(res.get("status"), "FAILED")
            self.assertIn("Simulated invalid logistics constraint error", str(res.get("error")))

            run_repo = LogisticsIntelligenceRunRepository(self.db, self.tenant_a)
            run_record = run_repo.get_by_id(str(res.get("logistics_run_id")))
            self.assertIsNotNone(run_record)
            if run_record:
                self.assertEqual(getattr(run_record, "status"), "FAILED")
        finally:
            if original_orch:
                setattr(logistics_service_module, "Phase6Orchestrator", original_orch)


if __name__ == "__main__":
    unittest.main()