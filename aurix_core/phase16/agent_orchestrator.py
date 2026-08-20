"""Governed Phase 16 supervisor and specialist-agent orchestration."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from aurix_core.intelligence.context import FactItem, FactPack, GroundingValidator
from aurix_core.intelligence.ai_gateway import AutonomousCopilotGateway, AIResponseContract
from aurix_core.intelligence.router import BusinessRouter, PageContext
from aurix_core.phase16.agent_contracts import (
    AgentRole,
    AgentRunResult,
    AgentToolCall,
    AutonomyLevel,
    ControlTowerQuery,
)
from aurix_core.phase16.case_service import create_case
from aurix_core.phase16.impact import ImpactPropagationService
from aurix_core.phase16.models import Phase16DecisionRecordModel
from aurix_core.tools.executor import DeterministicToolExecutor
from aurix_core.observability.metrics import MetricsRegistry


class Phase16Supervisor:
    """Routes Phase 16 requests through deterministic tools first.

    The supervisor may ask the existing AI gateway to explain or synthesize
    grounded facts, but it never directly executes operational writes.
    """

    _DOMAIN_AGENTS: Dict[str, AgentRole] = {
        "FORECASTING": AgentRole.INVENTORY,
        "INVENTORY": AgentRole.INVENTORY,
        "SUPPLY": AgentRole.SUPPLIER,
        "LOGISTICS": AgentRole.LOGISTICS,
        "NETWORK": AgentRole.LOGISTICS,
        "DECISION": AgentRole.PROCUREMENT,
        "ECONOMICS": AgentRole.FINANCE,
    }

    @classmethod
    def _specialists_for_query(
        cls,
        query: str,
    ) -> List[AgentRole]:
        lower = query.lower()
        roles: List[AgentRole] = [AgentRole.SUPERVISOR]

        if any(term in lower for term in ("supplier", "vendor", "po", "purchase", "rfq")):
            roles.extend([AgentRole.SUPPLIER, AgentRole.PROCUREMENT])
        if any(term in lower for term in ("inventory", "stock", "safety", "reorder")):
            roles.append(AgentRole.INVENTORY)
        if any(term in lower for term in ("bom", "mrp", "production", "capacity", "machine")):
            roles.append(AgentRole.MANUFACTURING)
        if any(term in lower for term in ("shipment", "carrier", "eta", "transport", "freight")):
            roles.append(AgentRole.LOGISTICS)
        if any(term in lower for term in ("customer order", "fulfill", "atp", "ctp", "promise", "allocation")):
            roles.append(AgentRole.FULFILLMENT)
        if any(term in lower for term in ("risk", "exposure", "disruption", "delay")):
            roles.append(AgentRole.RISK)
        if any(term in lower for term in ("cost", "working capital", "cash", "margin", "financial")):
            roles.append(AgentRole.FINANCE)
        if any(term in lower for term in ("what if", "scenario", "simulate")):
            roles.append(AgentRole.SCENARIO)

        deduped: List[AgentRole] = []
        for role in roles:
            if role not in deduped:
                deduped.append(role)
        return deduped

    @classmethod
    def _fact_pack_from_results(
        cls,
        tenant_id: str,
        query: str,
        routing: Any,
        results: List[AgentToolCall],
        result_payloads: List[Dict[str, Any]],
    ) -> FactPack:
        """Convert approved tool output into bounded, provenance-aware facts.

        Structured values are flattened only through simple JSON containers;
        arbitrary ORM/Python objects are never introspected.
        """
        facts: List[FactItem] = []
        provenance_refs: List[str] = []

        def add_fact(domain: str, metric_name: str, value: Any, provenance_id: Any) -> None:
            if len(facts) >= 100:
                return
            value_state = "UNAVAILABLE" if value is None else "OBSERVED"
            facts.append(
                FactItem(
                    domain=domain,
                    metric_name=metric_name,
                    entity_id=routing.resolved_entity_id,
                    value=value,
                    value_state=value_state,
                    freshness="LIVE",
                    provenance_id=provenance_id,
                )
            )

        def flatten(value: Any, prefix: str, domain: str, provenance_id: Any) -> None:
            if len(facts) >= 100:
                return
            if isinstance(value, (str, int, float, bool)) or value is None:
                add_fact(domain, prefix, value, provenance_id)
                return
            if isinstance(value, dict):
                for key, child in value.items():
                    child_prefix = f"{prefix}.{key}" if prefix else str(key)
                    flatten(child, child_prefix, domain, provenance_id)
                return
            if isinstance(value, list):
                for index, child in enumerate(value[:25]):
                    child_prefix = f"{prefix}[{index}]"
                    flatten(child, child_prefix, domain, provenance_id)

        for payload, tool_call in zip(result_payloads, results):
            domain = tool_call.capability or "PHASE16"
            provenance_id = tool_call.provenance.get("source_tables")
            flatten(payload, "", domain, provenance_id)
            for value in tool_call.provenance.values():
                if isinstance(value, (str, int, float)):
                    provenance_refs.append(str(value))
                elif isinstance(value, list):
                    provenance_refs.extend(str(item) for item in value[:20])

        return FactPack(
            pack_id=f"FACT-P16-{uuid.uuid4().hex[:10].upper()}",
            tenant_id=tenant_id,
            facts=facts,
            active_entity_id=routing.resolved_entity_id,
            allowable_entities={routing.resolved_entity_id.upper()} if routing.resolved_entity_id else set(),
            provenance_refs=provenance_refs[:100],
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    @classmethod
    def _record_decision(
        cls,
        db: Session,
        tenant_id: str,
        request: ControlTowerQuery,
        result: AgentRunResult,
    ) -> None:
        """Persist an auditable decision record without changing execution semantics."""
        fact_pack_id = result.provenance.get("fact_pack_id") if result.provenance else None
        record = Phase16DecisionRecordModel(
            id=f"DEC-{uuid.uuid4().hex[:16].upper()}",
            tenant_id=tenant_id,
            case_id=result.case_id,
            query=request.query,
            answer_source=result.answer_source,
            ai_provider=result.ai_provider,
            model_used=(result.provenance.get("ai_provenance", {}).get("model_used") if result.provenance else None),
            fact_pack_id=fact_pack_id,
            tool_calls_json=[call.model_dump(mode="json") for call in result.tool_calls],
            recommendation_json={"recommendations": result.recommendations, "impact": result.impact},
            provenance_json=result.provenance,
            status="PROPOSED",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(record)
        db.commit()
        MetricsRegistry.record_decision()
        result.provenance = {**result.provenance, "decision_record_id": record.id}

    @classmethod
    def run(
        cls,
        db: Session,
        tenant_id: str,
        request: ControlTowerQuery,
    ) -> AgentRunResult:
        routing = BusinessRouter.route(
            request.query,
            page_context=PageContext(
                active_entity_id=request.entity_id
            ) if request.entity_id else None,
        )

        specialists = cls._specialists_for_query(request.query)
        tool_calls: List[AgentToolCall] = []
        payloads: List[Dict[str, Any]] = []

        if (
            routing.target_capability
            and routing.target_tool
            and routing.query_type.value not in {"WRITE", "DESTRUCTIVE"}
        ):
            result = DeterministicToolExecutor.execute(
                db=db,
                tenant_id=tenant_id,
                query=request.query,
                routing=routing,
            )
            tool_call = AgentToolCall(
                tool_name=result.tool_name,
                capability=result.capability,
                success=result.success,
                provenance=result.provenance,
                limitations=result.limitations,
            )
            tool_calls.append(tool_call)
            MetricsRegistry.record_tool_call(result.success)
            if result.success:
                payloads.append(result.data)

            if result.success and not request.query.lower().startswith(
                ("why ", "explain ", "recommend ", "what if ")
            ):
                MetricsRegistry.record_query_resolution(
                    deterministic=True,
                    success=True,
                )
                MetricsRegistry.record_agent_run(True)
                agent_result = AgentRunResult(
                    success=True,
                    agent=AgentRole.SUPERVISOR,
                    autonomy_level=AutonomyLevel.RECOMMEND,
                    query=request.query,
                    answer=result.answer,
                    answer_source="AURIX_ENGINE",
                    specialist_agents=specialists,
                    tool_calls=tool_calls,
                    facts=result.data,
                    provenance={
                        "routing": routing.model_dump(),
                        "deterministic": True,
                    },
                )
                cls._record_decision(db, tenant_id, request, agent_result)
                return agent_result

        fact_pack = cls._fact_pack_from_results(
            tenant_id,
            request.query,
            routing,
            tool_calls,
            payloads,
        )

        MetricsRegistry.record_query_resolution(
            deterministic=False,
            success=True,
        )
        ai_response: AIResponseContract = AutonomousCopilotGateway.query(
            prompt=request.query,
            context=fact_pack,
            db=db,
        )

        grounding = GroundingValidator.validate(
            ai_response_text=(
                f"{ai_response.headline} {ai_response.explanation}"
            ),
            fact_pack=fact_pack,
        )

        if not grounding.is_grounded:
            MetricsRegistry.record_agent_run(True)
            agent_result = AgentRunResult(
                success=True,
                agent=AgentRole.SUPERVISOR,
                autonomy_level=request.autonomy_level,
                query=request.query,
                answer=(
                    "AURIX could not safely ground the requested "
                    "cross-domain reasoning. Deterministic facts are available."
                ),
                answer_source="AURIX_ENGINE",
                specialist_agents=specialists,
                tool_calls=tool_calls,
                facts={
                    "fact_count": len(fact_pack.facts),
                },
                ai_provider=None,
                warnings=grounding.violations,
                provenance={
                    "grounding": grounding.model_dump(),
                    "routing": routing.model_dump(),
                },
            )
            cls._record_decision(db, tenant_id, request, agent_result)
            return agent_result

        MetricsRegistry.record_agent_run(True)
        agent_result = AgentRunResult(
            success=True,
            agent=AgentRole.SUPERVISOR,
            autonomy_level=request.autonomy_level,
            query=request.query,
            answer=ai_response.explanation,
            answer_source=ai_response.answer_source,
            specialist_agents=specialists,
            tool_calls=tool_calls,
            facts=ai_response.verified_facts and {
                "verified_facts": ai_response.verified_facts
            } or {},
            ai_provider=ai_response.provider_used,
            warnings=ai_response.data_limitations,
            provenance={
                "routing": routing.model_dump(),
                "fact_pack_id": fact_pack.pack_id,
                "ai_provenance": ai_response.provenance,
            },
        )
        cls._record_decision(db, tenant_id, request, agent_result)
        return agent_result

    @classmethod
    def supplier_delay_case(
        cls,
        db: Session,
        tenant_id: str,
        supplier_id: str,
        delay_days: int,
        create: bool,
    ) -> Dict[str, Any]:
        impact = ImpactPropagationService.supplier_delay(
            db=db,
            tenant_id=tenant_id,
            supplier_id=supplier_id,
            delay_days=delay_days,
        )
        case_id = None
        if create:
            severity = (
                "HIGH"
                if impact["affected_sales_line_count"] > 0
                else "MEDIUM"
            )
            case_id = create_case(
                db,
                tenant_id,
                "SUPPLIER_DELAY",
                severity,
                f"Supplier {supplier_id} delay of {delay_days} day(s)",
                impact,
                {
                    "action_type": "ANALYZE_RECOVERY_OPTIONS",
                    "execution_authority": "PHASE14_ACTION_EXECUTOR",
                },
            )
        impact["case_id"] = case_id
        return impact
