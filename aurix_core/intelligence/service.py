"""Enterprise transactional service adapter for Phase 9 Executive Intelligence and AI Grounding."""

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from aurix_core.database.models.intelligence import (
    AIAuditLogModel,
    CapabilityStateModel,
    ConversationMessageModel,
    ConversationModel,
    ExecutiveSummaryModel,
    IntelligenceRunModel,
    IntelligenceSnapshotModel,
)
from aurix_core.database.repositories.intelligence import (
    AIAuditLogRepository,
    BusinessSignalRepository,
    CapabilityStateRepository,
    ConversationMessageRepository,
    ConversationRepository,
    ExecutiveSummaryRepository,
    IntelligenceRunRepository,
    IntelligenceSnapshotRepository,
    PrioritizedActionRepository,
)
from aurix_core.intelligence.ai_gateway import AIGateway, AIResponseContract
from aurix_core.intelligence.automation import AutomationEngine
from aurix_core.intelligence.context import ContextBuilder
from aurix_core.intelligence.discovery import CapabilityDiscoveryEngine
from aurix_core.intelligence.incremental import IncrementalMergeEngine, IncrementalUpdateReport
from aurix_core.intelligence.readiness import DataReadinessEngine, ReadinessAssessment
from aurix_core.intelligence.router import BusinessRouter, PageContext
from aurix_core.tools.executor import DeterministicToolExecutor
from aurix_core.observability.metrics import MetricsRegistry


class IntelligenceService:
    """Enterprise transactional service coordinating discovery, DAG execution, AI gateway, and memory."""

    def __init__(self, db: Session, tenant_id: str) -> None:
        self.db = db
        self.tenant_id = tenant_id

        # Repositories
        self.run_repo = IntelligenceRunRepository(db, tenant_id)
        self.cap_repo = CapabilityStateRepository(db, tenant_id)
        self.snapshot_repo = IntelligenceSnapshotRepository(db, tenant_id)
        self.signal_repo = BusinessSignalRepository(db, tenant_id)
        self.action_repo = PrioritizedActionRepository(db, tenant_id)
        self.summary_repo = ExecutiveSummaryRepository(db, tenant_id)
        self.conv_repo = ConversationRepository(db, tenant_id)
        self.msg_repo = ConversationMessageRepository(db, tenant_id)
        self.audit_repo = AIAuditLogRepository(db, tenant_id)

        # AI Gateway
        self.gateway = AIGateway()

    def _compute_dataset_hash(self, datasets: Dict[str, Any], config: Dict[str, Any]) -> str:
        """Computes a deterministic SHA-256 hash of datasets and configuration."""
        canonical_str = json.dumps({"datasets": datasets, "config": config}, sort_keys=True, default=str)
        return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()

    def run_autonomous_intelligence(
        self,
        canonical_datasets: Dict[str, List[Dict[str, Any]]],
        incremental_update: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Executes the autonomous discovery, incremental merge, and DAG execution pipeline atomically."""
        cfg_dict = config or {}
        dataset_hash = self._compute_dataset_hash(canonical_datasets, cfg_dict)

        # 1. Idempotency Check
        existing_run = self.run_repo.get_by_hash(dataset_hash)
        if existing_run and getattr(existing_run, "status", None) in (
            "COMPLETED",
            "PARTIAL_SUCCESS",
            "WAITING_FOR_INPUT",
        ):
            return {
                "status": getattr(existing_run, "status"),
                "idempotent_hit": True,
                "intelligence_run_id": getattr(existing_run, "id"),
                "dataset_hash": dataset_hash,
                "provenance": json.loads(getattr(existing_run, "provenance", "{}") or "{}"),
            }

        # 2. Initialize Execution Run Record
        run_id = f"RUN-INTEL-{uuid.uuid4().hex[:12].upper()}"
        run_rec = IntelligenceRunModel(
            id=run_id,
            tenant_id=self.tenant_id,
            dataset_hash=dataset_hash,
            status="EXECUTING",
            configuration=json.dumps(cfg_dict, default=str),
            provenance=json.dumps({"started_at": datetime.now(timezone.utc).isoformat()}, default=str),
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(run_rec)
        self.db.flush()

        try:
            # 3. Handle Incremental Merge if Provided
            merged_datasets = dict(canonical_datasets)
            incremental_report: Optional[IncrementalUpdateReport] = None

            if incremental_update:
                entity_name = incremental_update.get("entity_name", "demand_history")
                incoming_recs = incremental_update.get("records", [])
                key_fields = incremental_update.get("key_fields", ["sku_id", "date"])
                timestamp_field = incremental_update.get("timestamp_field", "date")
                existing_recs = merged_datasets.get(entity_name, [])

                merged_recs, incremental_report = IncrementalMergeEngine.diff_and_merge(
                    entity_name=entity_name,
                    existing_records=existing_recs,
                    incoming_records=incoming_recs,
                    key_fields=key_fields,
                    timestamp_field=timestamp_field,
                )
                merged_datasets[entity_name] = merged_recs

            # 4. Evaluate Record-Level Data Readiness
            readiness_map: Dict[str, ReadinessAssessment] = {}
            for entity_key, records in merged_datasets.items():
                req_fields = ["sku_id"]
                if "demand" in entity_key:
                    req_fields = ["sku_id", "date", "quantity"]
                elif "inventory" in entity_key:
                    req_fields = ["sku_id", "node_id", "on_hand_units", "lead_time_days"]
                elif "po" in entity_key or "purchase" in entity_key:
                    req_fields = ["po_id", "supplier_id", "promised_date", "actual_delivery_date"]
                elif "shipment" in entity_key:
                    req_fields = ["shipment_id", "carrier_id", "origin_node", "destination_node", "status"]
                elif "network" in entity_key:
                    req_fields = ["node_id", "node_type", "capacity"]
                elif "cost" in entity_key:
                    req_fields = ["sku_id", "unit_cost", "currency"]

                assessment = DataReadinessEngine.evaluate_entity_readiness(
                    entity_name=entity_key,
                    records=records,
                    required_fields=req_fields,
                )
                readiness_map[entity_key] = assessment

            # 5. Discover Capabilities & Prerequisite Status
            history_depths = {k: len(v) for k, v in merged_datasets.items()}
            discovery_report = CapabilityDiscoveryEngine.discover(
                readiness_map=readiness_map,
                history_depth_map=history_depths,
            )

# Persist Capability States
            for cap_name, cap_info in discovery_report.capabilities.items():
                dom_key = cap_info.domain.value.lower()
                readiness_item = readiness_map.get(dom_key, None)
                null_density = getattr(readiness_item, "null_density_pct", 0.0) if readiness_item else 0.0
                cap_rec = CapabilityStateModel(
                    id=f"CAP-{uuid.uuid4().hex[:10].upper()}",
                    tenant_id=self.tenant_id,
                    run_id=run_id,
                    capability_name=cap_name,
                    domain=cap_info.domain.value,
                    status=cap_info.status.value,
                    freshness_state=cap_info.freshness.value,
                    readiness_json=json.dumps({
                        "quality_score": cap_info.quality_score,
                        "completeness_pct": cap_info.completeness_pct,
                        "record_completeness_pct": cap_info.record_completeness_pct,
                        "null_density_pct": null_density,
                    }, default=str),
                    missing_prerequisites_json=json.dumps(cap_info.missing_prerequisites, default=str),
                )
                self.db.add(cap_rec)

            # 6. Execute Real Deterministic DAG Pipeline
            auto_result = AutomationEngine.execute_pipeline(
                discovery_report=discovery_report,
                canonical_datasets=merged_datasets,
                incremental_report=incremental_report,
                execution_context={"tenant_id": self.tenant_id, "run_id": run_id},
            )

            # 7. Persist Verified Intelligence Snapshot
            snap_rec = IntelligenceSnapshotModel(
                id=f"SNAP-{uuid.uuid4().hex[:10].upper()}",
                tenant_id=self.tenant_id,
                run_id=run_id,
                snapshot_json=json.dumps(auto_result.snapshot.model_dump(), default=str),
                summary_json=json.dumps({
                    "total_available": discovery_report.total_available,
                    "total_partial": discovery_report.total_partial,
                    "total_unavailable": discovery_report.total_unavailable,
                }, default=str),
                created_at=datetime.now(timezone.utc),
            )
            self.db.add(snap_rec)

            # 8. Persist Executive Summary
            exec_summary_rec = ExecutiveSummaryModel(
                id=f"EXSUM-{uuid.uuid4().hex[:10].upper()}",
                tenant_id=self.tenant_id,
                run_id=run_id,
                headline=f"Executive Intelligence: {len(auto_result.recomputed_capabilities)} Capabilities Active",
                narrative_json=json.dumps({
                    "overall_status": auto_result.overall_status.value,
                    "recomputed": auto_result.recomputed_capabilities,
                    "cached": auto_result.reused_cached_capabilities,
                }, default=str),
            )
            self.db.add(exec_summary_rec)

            # 9. Update Master Run Record Status
            final_status = auto_result.overall_status.value
            run_rec.status = final_status  # type: ignore[assignment]
            run_rec.provenance = json.dumps({  # type: ignore[assignment]
                "run_id": run_id,
                "dataset_hash": dataset_hash,
                "executed_capabilities": len(auto_result.executed_capabilities),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }, default=str)

            self.db.commit()

            return {
                "status": final_status,
                "idempotent_hit": False,
                "intelligence_run_id": run_id,
                "dataset_hash": dataset_hash,
                "discovery": discovery_report.model_dump(),
                "execution": auto_result.model_dump(),
            }

        except Exception as e:
            self.db.rollback()
            try:
                run_rec.status = "FAILED"  # type: ignore[assignment]
                run_rec.provenance = json.dumps({"error": str(e)}, default=str)  # type: ignore[assignment]
                self.db.commit()
            except Exception:
                pass
            return {
                "status": "FAILED",
                "intelligence_run_id": run_id,
                "error": str(e),
            }

    def ask_ai(
        self,
        query: str,
        conversation_id: Optional[str] = None,
        page_context: Optional[PageContext] = None,
        analytical_data: Optional[Dict[str, Any]] = None,
    ) -> AIResponseContract:
        """Processes user questions, queries conversation memory, builds fact-packs, and queries AI."""
        # 1. Resolve or Initialize Conversation Thread
        conv_id = conversation_id or f"CONV-{uuid.uuid4().hex[:10].upper()}"
        conv_rec = self.conv_repo.get_conversation(conv_id)

        if conv_rec is None:
            conv_rec = ConversationModel(
                id=conv_id,
                tenant_id=self.tenant_id,
                title=query[:60],
                active_domain=page_context.current_page if page_context else None,
                created_at=datetime.now(timezone.utc),
            )
            self.db.add(conv_rec)
            self.db.flush()

        # 2. Retrieve Recent Conversation History for Context & Referent Resolution
        prior_messages = self.msg_repo.list_by_conversation(conv_id, limit=20)
        conv_history = [{"role": m.role, "content": m.content} for m in prior_messages]

        # 3. Persist Current User Message
        user_msg = ConversationMessageModel(
            id=f"MSG-{uuid.uuid4().hex[:10].upper()}",
            tenant_id=self.tenant_id,
            conversation_id=conv_id,
            role="user",
            content=query,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(user_msg)
        self.db.flush()

        # 4. Retrieve Latest Tenant Intelligence Snapshot
        latest_snap_rec = self.snapshot_repo.get_latest_snapshot()
        latest_snapshot = None
        if latest_snap_rec and latest_snap_rec.snapshot_json:
            try:
                latest_snapshot = json.loads(str(latest_snap_rec.snapshot_json))
            except Exception:
                latest_snapshot = None

        # 5. Route Query using Active Page Context and Conversational History
        routing_decision = BusinessRouter.route(
            query=query,
            page_context=page_context,
            capability_states=(
                latest_snapshot.get("active_capabilities", {})
                if isinstance(latest_snapshot, dict)
                else {}
            ),
            conversation_history=conv_history,
        )

        # 6. Deterministic-first execution. A registered AURIX tool is
        # authoritative for direct READ queries and is never escalated to AI.
        if routing_decision.fast_path_eligible and routing_decision.target_tool:
            tool_result = DeterministicToolExecutor.execute(
                db=self.db,
                tenant_id=self.tenant_id,
                query=query,
                routing=routing_decision,
            )
            response_contract = AIResponseContract(
                response_id=f"RESP-AURIX-{uuid.uuid4().hex[:10].upper()}",
                response_type=routing_decision.query_type.value,
                headline="AURIX Engine Result",
                verified_facts=[tool_result.answer] if tool_result.answer else [],
                explanation=tool_result.answer,
                recommendations=[],
                data_limitations=tool_result.limitations,
                source="AURIX_ENGINE",
                answer_source="AURIX_ENGINE",
                evidence_quality="HIGH" if tool_result.success else "INSUFFICIENT_EVIDENCE",
                freshness="LIVE" if tool_result.success else "UNKNOWN",
                provider_used="AURIX_ENGINE",
                provider_status="LIVE",
                model_used="deterministic-tool",
                is_fallback=False,
                token_usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                provenance={
                    "tool_name": tool_result.tool_name,
                    "capability": tool_result.capability,
                    **tool_result.provenance,
                },
            )
        else:
            # 7. AI escalation path is only reached when AURIX cannot answer
            # deterministically. The same grounded FactPack is used for AI.
            fact_pack = ContextBuilder.build_fact_pack(
                tenant_id=self.tenant_id,
                routing_decision=routing_decision,
                analytical_data=analytical_data,
                page_context=page_context,
            )

            response_contract = self.gateway.process_query(
                fact_pack=fact_pack,
                routing_decision=routing_decision,
                db=self.db,
            )

        # 8. Persist Assistant Response Message
        asst_msg = ConversationMessageModel(
            id=f"MSG-{uuid.uuid4().hex[:10].upper()}",
            tenant_id=self.tenant_id,
            conversation_id=conv_id,
            role="assistant",
            content=f"{response_contract.headline}\n\n{response_contract.explanation}",
            provenance_json=json.dumps(response_contract.provenance, default=str),
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(asst_msg)

        # 9. Record resolution telemetry and audit metadata.
        deterministic_answer = response_contract.answer_source == "AURIX_ENGINE"
        MetricsRegistry.record_query_resolution(
            deterministic=deterministic_answer,
            success=deterministic_answer and bool(response_contract.explanation)
            or not deterministic_answer,
        )

        audit_rec = AIAuditLogModel(
            id=f"AUDIT-{uuid.uuid4().hex[:10].upper()}",
            tenant_id=self.tenant_id,
            conversation_id=conv_id,
            query_type=routing_decision.query_type.value,
            provider_name=response_contract.provider_used,
            model_name=response_contract.model_used,
            status=("DETERMINISTIC" if deterministic_answer else "SUCCESS"),
            grounding_status=(
                "DETERMINISTIC_FAST_PATH"
                if deterministic_answer
                else (
                    "VALIDATED"
                    if not response_contract.is_fallback
                    else "FALLBACK"
                )
            ),
            routing_meta_json=json.dumps(routing_decision.model_dump(), default=str),
            token_usage_json=json.dumps(response_contract.token_usage, default=str),
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(audit_rec)
        self.db.commit()

        return response_contract