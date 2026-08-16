"""Comprehensive Unit, Integration, Persistence, and Adversarial Test Suite for Phase 9 Intelligence."""

import unittest
from datetime import datetime, timezone
from typing import Any, Dict
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Database Engine & Metadata Imports
from aurix_core.database.engine import Base
from aurix_core.database.models import (
    economics as economics_models,
    forecasting,
    ingestion,
    intelligence as intelligence_models,
    inventory_intelligence,
    logistics_intelligence,
    network_intelligence,
    supply_chain,
    supply_intelligence,
)
from aurix_core.database.repositories.intelligence import (
    ConversationMessageRepository,
    ConversationRepository,
    IntelligenceRunRepository,
    IntelligenceSnapshotRepository,
)

# Core Intelligence Modules
from aurix_core.intelligence.ai_gateway import AIGateway
from aurix_core.intelligence.automation import AutomationEngine, ExecutionStatus
from aurix_core.intelligence.causal import EvidenceChainBuilder
from aurix_core.intelligence.config import IntelligenceConfiguration
from aurix_core.intelligence.context import FactItem, FactPack, GroundingValidator
from aurix_core.intelligence.discovery import (
    CapabilityDiscoveryEngine,
    CapabilityStatus,
)
from aurix_core.intelligence.incremental import (
    IncrementalMergeEngine,
)
from aurix_core.intelligence.narrative import ExecutiveNarrativeGenerator
from aurix_core.intelligence.orchestrator import Phase9Orchestrator
from aurix_core.intelligence.priorities import ActionPrioritizer
from aurix_core.intelligence.readiness import (
    DataReadinessEngine,
    FreshnessState,
)
from aurix_core.intelligence.router import (
    BusinessRouter,
    QueryType,
)
from aurix_core.intelligence.service import IntelligenceService
from aurix_core.intelligence.signals import SignalExtractor
from aurix_core.schema.phase5_contract import TrackedValue, ValueState
from aurix_core.schema.phase10_contract import Phase10InputContract
from aurix_core.schema.phase11_contract import (
    BusinessSignal,
    EvidenceType,
    Phase11InputContract,
    SignalDomain,
    SignalSeverity,
)


class TestPhase9IntelligenceCore(unittest.TestCase):
    """Unit tests for analytical intelligence, signal extraction, prioritization, and narratives."""

    def setUp(self) -> None:
        self.config = IntelligenceConfiguration()

    def test_01_configuration_clamping_and_defaults(self) -> None:
        overrides = {
            "severity_weight": -0.5,
            "max_prioritized_actions": -10,
            "enable_ai_interpretation": True,
        }
        cfg = IntelligenceConfiguration(overrides)
        self.assertEqual(cfg.severity_weight, 0.0)
        self.assertEqual(cfg.max_prioritized_actions, 1)
        self.assertTrue(cfg.enable_ai_interpretation)

    def test_02_signal_extractor_multi_phase(self) -> None:
        p8_data: Dict[str, Any] = {
            "status": "COMPUTABLE",
            "portfolio_financials_by_currency": {},
            "sku_working_capital": {
                "SKU-HIGH-RISK": [
                    {
                        "sku_id": "SKU-HIGH-RISK",
                        "node_id": "DC-01",
                        "currency": "USD",
                        "total_inventory_value": {"value": 150000.0, "state": "DERIVED", "source": "INV"},
                        "cycle_stock_value": {"value": 75000.0, "state": "DERIVED", "source": "CYCLE"},
                        "safety_stock_value": {"value": 75000.0, "state": "DERIVED", "source": "SAFETY"},
                        "excess_capital_tied": {"value": 0.0, "state": "DERIVED", "source": "EXCESS"},
                        "annual_holding_cost": {"value": 22500.0, "state": "DERIVED", "source": "HOLDING"},
                        "financial_risk_level": "HIGH",
                    }
                ]
            },
            "sku_tco": {},
            "scenarios": {},
            "limitations": [],
            "provenance": {"phase8_run_id": "RUN-P8-001"},
        }
        p8_contract = Phase10InputContract(**p8_data)
        signals = SignalExtractor.extract_signals(phase8_contract=p8_contract, config=self.config)

        self.assertEqual(len(signals), 1)
        sig = signals[0]
        self.assertEqual(sig.domain, SignalDomain.ECONOMICS)
        self.assertEqual(sig.severity, SignalSeverity.HIGH)
        self.assertEqual(sig.affected_entity_id, "SKU-HIGH-RISK@DC-01")

        exposure = sig.financial_exposure
        self.assertIsNotNone(exposure)
        assert exposure is not None
        self.assertEqual(exposure.value, 150000.0)

    def test_03_action_prioritizer_ranking_and_currency(self) -> None:
        sig_crit = BusinessSignal(
            signal_id="SIG-01",
            signal_type="CRITICAL_EXPOSURE",
            domain=SignalDomain.ECONOMICS,
            severity=SignalSeverity.CRITICAL,
            affected_entity_id="DC-CRIT",
            description="Critical financial exposure.",
            evidence_quality=EvidenceType.DERIVED,
            source_phase="Phase 8",
            source_metrics={},
            financial_exposure=TrackedValue(value=200000.0, state=ValueState.DERIVED, source="TEST"),
            provenance={"currency": "USD"},
        )

        sig_inr = BusinessSignal(
            signal_id="SIG-02",
            signal_type="HIGH_EXPOSURE",
            domain=SignalDomain.INVENTORY,
            severity=SignalSeverity.HIGH,
            affected_entity_id="DC-INR",
            description="High exposure INR.",
            evidence_quality=EvidenceType.OBSERVED,
            source_phase="Phase 4",
            source_metrics={},
            financial_exposure=TrackedValue(value=8000000.0, state=ValueState.DERIVED, source="TEST"),
            provenance={"currency": "INR"},
        )

        actions = ActionPrioritizer.prioritize_signals([sig_inr, sig_crit], config=self.config)
        self.assertEqual(len(actions), 2)
        self.assertEqual(actions[0].rank, 1)
        self.assertEqual(actions[0].risk_level, "CRITICAL")
        self.assertEqual(actions[1].rank, 2)

    def test_04_action_prioritizer_unavailable_financial_exposure(self) -> None:
        sig_unavail = BusinessSignal(
            signal_id="SIG-UNAVAIL",
            signal_type="NO_COST_SIGNAL",
            domain=SignalDomain.INVENTORY,
            severity=SignalSeverity.MODERATE,
            affected_entity_id="SKU-NOCOST",
            description="Missing cost metric.",
            evidence_quality=EvidenceType.OBSERVED,
            source_phase="Phase 4",
            source_metrics={},
            financial_exposure=TrackedValue(value=None, state=ValueState.UNAVAILABLE, source="UNAVAILABLE"),
        )

        actions = ActionPrioritizer.prioritize_signals([sig_unavail], config=self.config)
        self.assertEqual(len(actions), 1)
        impact = actions[0].financial_impact
        self.assertIsNotNone(impact)
        assert impact is not None
        self.assertEqual(impact.state, ValueState.UNAVAILABLE)

    def test_05_evidence_chain_builder(self) -> None:
        sig = BusinessSignal(
            signal_id="SIG-CHAIN",
            signal_type="WORKING_CAPITAL_EXPOSURE",
            domain=SignalDomain.ECONOMICS,
            severity=SignalSeverity.HIGH,
            affected_entity_id="SKU-CHAIN@DC-1",
            description="High working capital.",
            evidence_quality=EvidenceType.DERIVED,
            source_phase="Phase 8",
            source_metrics={"inv_val": TrackedValue(value=50000.0, state=ValueState.DERIVED, source="TEST")},
            financial_exposure=TrackedValue(value=50000.0, state=ValueState.DERIVED, source="TEST"),
        )

        chains = EvidenceChainBuilder.build_evidence_chains([sig], config=self.config)
        self.assertEqual(len(chains), 1)
        self.assertEqual(chains[0].primary_signal_id, "SIG-CHAIN")
        self.assertGreaterEqual(len(chains[0].steps), 2)

    def test_06_executive_narrative_generator_data_sufficiency_boundaries(self) -> None:
        sig = BusinessSignal(
            signal_id="SIG-NARR",
            signal_type="CRITICAL_STOCKOUT_RISK",
            domain=SignalDomain.INVENTORY,
            severity=SignalSeverity.CRITICAL,
            affected_entity_id="DC-NARR",
            description="Critical stockout imminent.",
            evidence_quality=EvidenceType.OBSERVED,
            source_phase="Phase 4",
            source_metrics={},
        )

        summary_crit = ExecutiveNarrativeGenerator.generate_summary([sig], [], [], config=self.config)
        self.assertEqual(summary_crit.overall_health_status, "CRITICAL_EXPOSURE")

        summary_adequate = ExecutiveNarrativeGenerator.generate_summary(
            [], [], [], config=self.config, data_sufficiency="ADEQUATE"
        )
        self.assertEqual(summary_adequate.overall_health_status, "STABLE_WITH_NO_MATERIAL_EXCEPTIONS")

        summary_insufficient = ExecutiveNarrativeGenerator.generate_summary(
            [], [], [], config=self.config, data_sufficiency="INSUFFICIENT"
        )
        self.assertEqual(summary_insufficient.overall_health_status, "INSUFFICIENT_EVIDENCE")

    def test_07_orchestrator_and_contract_roundtrip(self) -> None:
        p8_data: Dict[str, Any] = {
            "status": "COMPUTABLE",
            "portfolio_financials_by_currency": {},
            "sku_working_capital": {
                "SKU-E2E": [
                    {
                        "sku_id": "SKU-E2E",
                        "node_id": "DC-E2E",
                        "currency": "USD",
                        "total_inventory_value": {"value": 300000.0, "state": "DERIVED", "source": "INV"},
                        "cycle_stock_value": {"value": 150000.0, "state": "DERIVED", "source": "CYCLE"},
                        "safety_stock_value": {"value": 150000.0, "state": "DERIVED", "source": "SAFETY"},
                        "excess_capital_tied": {"value": 0.0, "state": "DERIVED", "source": "EXCESS"},
                        "annual_holding_cost": {"value": 45000.0, "state": "DERIVED", "source": "HOLDING"},
                        "financial_risk_level": "CRITICAL",
                    }
                ]
            },
            "sku_tco": {},
            "scenarios": {},
            "limitations": [],
            "provenance": {"phase8_run_id": "RUN-P8-E2E"},
        }

        orch = Phase9Orchestrator(phase8_economics_output=p8_data)
        res_dict = orch.execute()

        self.assertEqual(res_dict["status"], "COMPUTABLE")
        self.assertEqual(len(res_dict["signals"]), 1)

        reconstructed = Phase11InputContract(**res_dict)
        self.assertEqual(reconstructed.status, "COMPUTABLE")

    def test_08_orchestrator_missing_upstream_inputs(self) -> None:
        orch = Phase9Orchestrator()
        res = orch.execute()
        self.assertEqual(res["status"], "USER_INPUT_REQUIRED")
        self.assertEqual(len(res["missing_inputs"]), 1)


class TestPhase9ReadinessAndDiscovery(unittest.TestCase):
    """Tests evaluating readiness, freshness, record-level completeness, and discovery prerequisites."""

    def test_09_freshness_evaluation_boundaries(self) -> None:
        ref_time = datetime(2026, 8, 14, 12, 0, 0, tzinfo=timezone.utc)

        # 1. Live (< 24 hours)
        live_ts = "2026-08-14T06:00:00Z"
        state, age = DataReadinessEngine.evaluate_freshness(live_ts, reference_time=ref_time)
        self.assertEqual(state, FreshnessState.LIVE)
        self.assertEqual(age, 6.0)

        # 2. Stale (between 7 and 30 days)
        stale_ts = "2026-07-25T12:00:00Z"
        state, age = DataReadinessEngine.evaluate_freshness(stale_ts, reference_time=ref_time)
        self.assertEqual(state, FreshnessState.STALE)

        # 3. Unknown (None timestamp)
        state_none, age_none = DataReadinessEngine.evaluate_freshness(None, reference_time=ref_time)
        self.assertEqual(state_none, FreshnessState.UNKNOWN)
        self.assertIsNone(age_none)

    def test_10_record_level_completeness_and_null_density(self) -> None:
        now_iso = datetime.now(timezone.utc).isoformat()
        records = [
            {"sku_id": "SKU-1", "date": now_iso[:10], "quantity": 100.0 if i < 6 else None}
            for i in range(10)
        ]
        meta = {"source_system": "WMS", "source_health": "HEALTHY", "source_timestamp": now_iso}

        res = DataReadinessEngine.evaluate_entity_readiness(
            entity_name="demand_history",
            records=records,
            required_fields=["sku_id", "date", "quantity"],
            source_meta=meta,
        )

        self.assertFalse(res.available)
        self.assertIn("quantity", res.partially_populated_fields)
        self.assertEqual(res.null_density_pct, 13.33)
        self.assertGreater(res.record_completeness_pct, 80.0)

    def test_11_capability_discovery_partial_dataset(self) -> None:
        now_iso = datetime.now(timezone.utc).isoformat()
        readiness_map = {
            "demand_history": DataReadinessEngine.evaluate_entity_readiness(
                entity_name="demand_history",
                records=[{"sku_id": "SKU-1", "date": now_iso[:10], "quantity": 50.0}],
                required_fields=["sku_id", "date", "quantity"],
                source_meta={"source_timestamp": now_iso},
            )
        }
        history_depths = {"demand_history": 10}

        report = CapabilityDiscoveryEngine.discover(readiness_map, history_depth_map=history_depths)

        self.assertIn("DEMAND_CLASSIFICATION", report.capabilities)
        self.assertIn("SAFETY_STOCK_ROP", report.capabilities)
        self.assertEqual(report.capabilities["DEMAND_CLASSIFICATION"].status, CapabilityStatus.AVAILABLE)
        self.assertEqual(report.capabilities["DEMAND_FORECASTING"].status, CapabilityStatus.AVAILABLE)
        self.assertEqual(report.capabilities["SAFETY_STOCK_ROP"].status, CapabilityStatus.UNAVAILABLE)
        self.assertEqual(report.overall_status, "PARTIAL_SUCCESS")


class TestPhase9IncrementalAndAutomation(unittest.TestCase):
    """Tests evaluating recurring data updates, historical corrections, and automated DAG real execution."""

    def test_12_incremental_merge_and_historical_correction(self) -> None:
        existing = [
            {"sku_id": "SKU-1", "date": "2026-01-01", "quantity": 1000.0},
            {"sku_id": "SKU-1", "date": "2026-02-01", "quantity": 1100.0},
        ]
        incoming = [
            {"sku_id": "SKU-1", "date": "2026-01-01", "quantity": 1080.0},
            {"sku_id": "SKU-1", "date": "2026-02-01", "quantity": 1100.0},
            {"sku_id": "SKU-1", "date": "2026-03-01", "quantity": 1250.0},
        ]

        merged, report = IncrementalMergeEngine.diff_and_merge(
            entity_name="demand_history",
            existing_records=existing,
            incoming_records=incoming,
            key_fields=["sku_id", "date"],
            value_fields=["quantity"],
        )

        self.assertEqual(len(merged), 3)
        self.assertEqual(report.new_records_count, 1)
        self.assertEqual(report.duplicates_count, 1)
        self.assertEqual(report.corrections_count, 1)
        self.assertTrue(report.requires_recomputation)
        self.assertIn("DEMAND_FORECASTING", report.affected_capabilities)
        self.assertIn("SUPPLIER_PERFORMANCE_RISK", report.unaffected_capabilities)

        jan_rec = [r for r in merged if r["date"] == "2026-01-01"][0]
        self.assertEqual(jan_rec["quantity"], 1080.0)
        self.assertEqual(jan_rec["_version"], 2)

    def test_13_real_dag_execution_and_mathematical_outputs(self) -> None:
        now_iso = datetime.now(timezone.utc).isoformat()
        demand_data = [
            {"sku_id": "SKU-REAL", "date": f"2026-0{i}-01", "quantity": 100.0 + i * 15}
            for i in range(1, 9)
        ]
        inv_data = [
            {"sku_id": "SKU-REAL", "node_id": "DC-MAIN", "on_hand_units": 450.0, "lead_time_days": 10.0}
        ]
        cost_data = [
            {"sku_id": "SKU-REAL", "unit_cost": 25.0, "currency": "USD"}
        ]

        canonical = {
            "demand_history": demand_data,
            "inventory_levels": inv_data,
            "item_costs": cost_data,
        }

        readiness_map = {
            k: DataReadinessEngine.evaluate_entity_readiness(
                entity_name=k,
                records=v,
                required_fields=["sku_id"],
                source_meta={"source_timestamp": now_iso},
            )
            for k, v in canonical.items()
        }

        discovery = CapabilityDiscoveryEngine.discover(readiness_map, history_depth_map={"demand_history": 8})
        res = AutomationEngine.execute_pipeline(discovery_report=discovery, canonical_datasets=canonical)

        self.assertIn(res.overall_status, (ExecutionStatus.COMPLETED, ExecutionStatus.PARTIAL_SUCCESS))

        # 1. Assert Real Forecasting Math
        fc_res = res.executed_capabilities["DEMAND_FORECASTING"]
        self.assertEqual(fc_res.status, ExecutionStatus.COMPLETED)
        assert isinstance(fc_res.output_payload, dict)
        forecast_item = fc_res.output_payload["sku_forecasts"]["SKU-REAL"]
        self.assertGreater(forecast_item["point_forecast"], 100.0)
        self.assertGreater(forecast_item["forecast_upper_bound"], forecast_item["point_forecast"])

        # 2. Assert Real Inventory Safety Stock / ROP Math
        ss_res = res.executed_capabilities["SAFETY_STOCK_ROP"]
        self.assertEqual(ss_res.status, ExecutionStatus.COMPLETED)
        assert isinstance(ss_res.output_payload, dict)
        ss_item = ss_res.output_payload["inventory_policies"]["SKU-REAL@DC-MAIN"]
        self.assertGreater(ss_item["safety_stock"], 0)
        self.assertGreater(ss_item["reorder_point"], ss_item["safety_stock"])

        # 3. Assert Real Working Capital Calculations
        wc_res = res.executed_capabilities["WORKING_CAPITAL_TCO"]
        self.assertEqual(wc_res.status, ExecutionStatus.COMPLETED)
        assert isinstance(wc_res.output_payload, dict)
        self.assertEqual(wc_res.output_payload["portfolio_working_capital"], 450.0 * 25.0)


class TestPhase9RouterAndGrounding(unittest.TestCase):
    """Tests evaluating business routing, multi-turn conversational memory, and approved math derivations."""

    def test_14_router_fast_path_and_safety_gating(self) -> None:
        read_dec = BusinessRouter.route("What is the current safety stock for SKU-01?")
        self.assertEqual(read_dec.query_type, QueryType.READ)
        self.assertTrue(read_dec.fast_path_eligible)
        self.assertFalse(read_dec.requires_ai)
        self.assertEqual(read_dec.resolved_entity_id, "SKU-01")

        destruct_dec = BusinessRouter.route("Drop table inventory_levels;")
        self.assertEqual(destruct_dec.query_type, QueryType.DESTRUCTIVE)
        self.assertFalse(destruct_dec.capability_available)
        self.assertIsNotNone(destruct_dec.rejection_reason)

    def test_15_conversational_memory_multi_turn_referent_resolution(self) -> None:
        conv_history = [
            {"role": "user", "content": "What is the stock position of SKU-999?"},
            {"role": "assistant", "content": "SKU-999 has 1200 units on hand at DC-MAIN."},
        ]

        follow_up_dec = BusinessRouter.route(
            query="What if we increase it by 20%?",
            page_context=None,
            conversation_history=conv_history,
        )

        self.assertEqual(follow_up_dec.query_type, QueryType.SIMULATE)
        self.assertEqual(follow_up_dec.resolved_entity_id, "SKU-999")
        self.assertEqual(follow_up_dec.context_source, "CONVERSATION_MEMORY")

    def test_16_grounding_validator_approved_derivations_and_rejections(self) -> None:
        fact_pack = FactPack(
            pack_id="FACT-01",
            tenant_id="tenant_alpha",
            facts=[
                FactItem(domain="INVENTORY", metric_name="on_hand", entity_id="SKU-100", value=1200.0),
                FactItem(domain="FORECASTING", metric_name="daily_demand", entity_id="SKU-100", value=200.0),
            ],
            active_entity_id="SKU-100",
            allowable_entities={"SKU-100"},
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

        approved_text = "SKU-100 has 1200.0 on hand with 200.0 daily demand, yielding 6.0 days of coverage."
        valid_res = GroundingValidator.validate(approved_text, fact_pack)
        self.assertTrue(valid_res.is_grounded)
        self.assertIn(6.0, valid_res.approved_derived_numbers)

        hallucinated_text = "SUP-FAKE reports coverage is 14.0 days for SKU-100."
        invalid_res = GroundingValidator.validate(hallucinated_text, fact_pack)
        self.assertFalse(invalid_res.is_grounded)
        self.assertTrue(invalid_res.fallback_required)
        self.assertIn(14.0, invalid_res.unsupported_numbers)
        self.assertIn("SUP-FAKE", invalid_res.unsupported_entities)

    def test_17_ai_gateway_failover_and_metadata_preservation(self) -> None:
        fact_pack = FactPack(
            pack_id="FACT-GATEWAY",
            tenant_id="tenant_alpha",
            facts=[
                FactItem(
                    domain="SUPPLY",
                    metric_name="otd_rate",
                    entity_id="SUP-A",
                    value=92.5,
                    freshness="STALE",
                    value_state="OBSERVED",
                )
            ],
            active_entity_id="SUP-A",
            allowable_entities={"SUP-A"},
            generated_at=datetime.now(timezone.utc).isoformat(),
        )
        routing = BusinessRouter.route("Explain performance for SUP-A")

        gateway = AIGateway(simulate_gemini_failure=True, simulate_groq_failure=True, simulate_workers_failure=True)
        resp = gateway.process_query(fact_pack, routing)

        self.assertIsNotNone(resp)
        self.assertTrue(resp.is_fallback)
        self.assertEqual(resp.provider_used, "DETERMINISTIC_FALLBACK")
        self.assertEqual(resp.freshness, "STALE")


class TestPhase9PersistenceAndSecurity(unittest.TestCase):
    """Integration tests verifying database persistence, multi-tenancy, idempotency, and conversation security."""

    def setUp(self) -> None:
        self.engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        _ = supply_chain.__name__
        _ = ingestion.__name__
        _ = forecasting.__name__
        _ = inventory_intelligence.__name__
        _ = supply_intelligence.__name__
        _ = logistics_intelligence.__name__
        _ = network_intelligence.__name__
        _ = economics_models.__name__
        _ = intelligence_models.__name__

        Base.metadata.create_all(bind=self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine, autocommit=False, autoflush=False)
        self.db: Session = self.SessionLocal()

        self.tenant_a = "tenant_alpha"
        self.tenant_b = "tenant_beta"
        now_iso = datetime.now(timezone.utc).isoformat()[:10]
        self.mock_data = {
            "demand_history": [
                {"sku_id": "SKU-TEST", "date": f"{now_iso}", "quantity": 100.0 + i * 10}
                for i in range(1, 10)
            ]
        }

    def tearDown(self) -> None:
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)

    def test_18_intelligence_persistence_and_idempotency(self) -> None:
        service_a = IntelligenceService(self.db, self.tenant_a)
        res1 = service_a.run_autonomous_intelligence(self.mock_data)

        self.assertIn(res1.get("status"), ("COMPLETED", "PARTIAL_SUCCESS", "WAITING_FOR_INPUT"))
        self.assertFalse(res1.get("idempotent_hit"))

        run_repo = IntelligenceRunRepository(self.db, self.tenant_a)
        run_rec = run_repo.get_by_id(str(res1.get("intelligence_run_id")))
        self.assertIsNotNone(run_rec)

        res2 = service_a.run_autonomous_intelligence(self.mock_data)
        self.assertTrue(res2.get("idempotent_hit"))
        self.assertEqual(res1.get("intelligence_run_id"), res2.get("intelligence_run_id"))

        run_repo_b = IntelligenceRunRepository(self.db, self.tenant_b)
        snap_repo_b = IntelligenceSnapshotRepository(self.db, self.tenant_b)
        self.assertIsNone(run_repo_b.get_by_id(str(res1.get("intelligence_run_id"))))
        self.assertIsNone(snap_repo_b.get_latest_snapshot())

    def test_19_conversation_memory_and_cross_tenant_security(self) -> None:
        service_a = IntelligenceService(self.db, self.tenant_a)
        conv_id = "CONV-SECURE-001"

        resp_a1 = service_a.ask_ai("What is the status of SKU-TEST?", conversation_id=conv_id)
        self.assertIsNotNone(resp_a1)

        resp_a2 = service_a.ask_ai("Why is it at risk?", conversation_id=conv_id)
        self.assertIsNotNone(resp_a2)

        conv_repo_a = ConversationRepository(self.db, self.tenant_a)
        msg_repo_a = ConversationMessageRepository(self.db, self.tenant_a)
        self.assertIsNotNone(conv_repo_a.get_conversation(conv_id))
        self.assertEqual(len(msg_repo_a.list_by_conversation(conv_id)), 4)

        conv_repo_b = ConversationRepository(self.db, self.tenant_b)
        msg_repo_b = ConversationMessageRepository(self.db, self.tenant_b)
        self.assertIsNone(conv_repo_b.get_conversation(conv_id))
        self.assertEqual(len(msg_repo_b.list_by_conversation(conv_id)), 0)


if __name__ == "__main__":
    unittest.main()