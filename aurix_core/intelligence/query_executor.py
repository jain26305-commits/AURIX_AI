"""
Deterministic AURIX Query Execution Engine.

Executes an explicit DeterministicQueryPlan against registered, read-only
AURIX tools and returns an auditable execution bundle.

This layer deliberately separates:
    Query understanding
        -> Query planning
        -> Query execution
        -> Reasoning
        -> Answer composition

No LLM is used here.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from aurix_core.intelligence.query_plan import (
    DeterministicOperation,
    DeterministicQueryPlan,
    QueryEntity,
)
from aurix_core.tools.contracts import ToolRequest, ToolResult
from aurix_core.tools.registry import ToolRegistry


class QueryExecutionRecord(BaseModel):
    """Auditable execution record for one deterministic operation."""

    operation_id: str
    tool_name: str
    capability: Optional[str] = None
    entity_id: Optional[str] = None

    success: bool = False
    skipped: bool = False

    answer: str = ""
    data: Dict[str, Any] = Field(default_factory=dict)
    limitations: List[str] = Field(default_factory=list)
    provenance: Dict[str, Any] = Field(default_factory=dict)

    depends_on: List[str] = Field(default_factory=list)


class DeterministicQueryExecutionResult(BaseModel):
    """Complete deterministic execution result for a query plan."""

    query: str
    success: bool = False

    records: List[QueryExecutionRecord] = Field(default_factory=list)

    successful_operations: List[str] = Field(default_factory=list)
    failed_operations: List[str] = Field(default_factory=list)
    skipped_operations: List[str] = Field(default_factory=list)

    entities_executed: List[str] = Field(default_factory=list)

    evidence: List[Dict[str, Any]] = Field(default_factory=list)
    data: Dict[str, Any] = Field(default_factory=dict)

    limitations: List[str] = Field(default_factory=list)

    provenance: Dict[str, Any] = Field(default_factory=dict)


class DeterministicQueryExecutor:
    """
    Executes deterministic query plans against the AURIX ToolRegistry.

    Design rules:
    - never executes side-effecting tools
    - respects operation dependencies
    - expands multi-entity operations
    - keeps every tool result auditable
    - never invents missing data
    """

    @staticmethod
    def _entity_candidates(
        operation: DeterministicOperation,
        plan: DeterministicQueryPlan,
    ) -> List[Optional[QueryEntity]]:
        """
        Resolve the entity scope for an operation.

        A single operation such as supplier.performance can therefore be
        expanded across multiple entities for comparison/ranking workflows.
        """

        if operation.entity is not None:
            return [operation.entity]

        definition = ToolRegistry.get(operation.tool_name)

        if definition is None:
            return [None]

        if not definition.requires_entity:
            return [None]

        if plan.entities:
            return list(plan.entities)

        return [None]

    @staticmethod
    def _operation_is_ready(
        operation: DeterministicOperation,
        completed: Dict[str, QueryExecutionRecord],
    ) -> tuple[bool, Optional[str]]:
        """Verify that every required dependency has completed successfully."""

        for dependency in operation.depends_on:
            dependency_record = completed.get(dependency)

            if dependency_record is None:
                return False, f"MISSING_DEPENDENCY:{dependency}"

            if not dependency_record.success:
                return False, f"DEPENDENCY_FAILED:{dependency}"

        return True, None

    @staticmethod
    def _execute_one(
        plan: DeterministicQueryPlan,
        operation: DeterministicOperation,
        entity: Optional[QueryEntity],
        db,
        tenant_id: str,
    ) -> QueryExecutionRecord:
        """Execute one concrete operation/entity pair."""

        definition = ToolRegistry.get(operation.tool_name)

        entity_id = entity.entity_id if entity else None

        if definition is None:
            return QueryExecutionRecord(
                operation_id=operation.operation_id,
                tool_name=operation.tool_name,
                capability=operation.capability,
                entity_id=entity_id,
                success=False,
                answer="The requested deterministic tool is not registered.",
                limitations=["TOOL_NOT_REGISTERED"],
                depends_on=list(operation.depends_on),
            )

        if definition.side_effect:
            return QueryExecutionRecord(
                operation_id=operation.operation_id,
                tool_name=operation.tool_name,
                capability=operation.capability,
                entity_id=entity_id,
                success=False,
                answer="Side-effecting tools are not permitted in deterministic query execution.",
                limitations=["SIDE_EFFECT_TOOL_BLOCKED"],
                depends_on=list(operation.depends_on),
            )

        if definition.requires_entity and not entity_id:
            return QueryExecutionRecord(
                operation_id=operation.operation_id,
                tool_name=operation.tool_name,
                capability=operation.capability,
                entity_id=None,
                success=False,
                answer="A specific entity is required for this deterministic operation.",
                limitations=["ENTITY_REQUIRED"],
                depends_on=list(operation.depends_on),
            )

        request_parameters = dict(operation.parameters or {})

        if entity_id:
            request_parameters.setdefault("entity_id", entity_id)

        request = ToolRequest(
            tenant_id=tenant_id,
            query=plan.query,
            tool_name=operation.tool_name,
            entity_id=entity_id,
            entity_type=entity.entity_type if entity else None,
            parameters=request_parameters,
        )

        result: ToolResult = ToolRegistry.execute(
            db=db,
            request=request,
        )

        return QueryExecutionRecord(
            operation_id=operation.operation_id,
            tool_name=operation.tool_name,
            capability=operation.capability,
            entity_id=entity_id,
            success=bool(result.success),
            answer=result.answer or "",
            data=dict(result.data or {}),
            limitations=list(result.limitations or []),
            provenance=dict(result.provenance or {}),
            depends_on=list(operation.depends_on),
        )

    @classmethod
    def execute(
        cls,
        plan: DeterministicQueryPlan,
        db,
        tenant_id: str,
    ) -> DeterministicQueryExecutionResult:
        """
        Execute the supplied deterministic query plan.

        Operations are executed in declared dependency order. The executor
        remains tolerant of a partially executable plan so later reasoning
        layers can decide whether escalation is required.
        """

        result = DeterministicQueryExecutionResult(
            query=plan.query,
            success=False,
            provenance={
                "planner": "DeterministicQueryPlanner",
                "executor": "DeterministicQueryExecutor",
                "tenant_id": tenant_id,
                "intent": plan.intent.value,
                "operation_count": len(plan.operations),
            },
        )

        completed: Dict[str, QueryExecutionRecord] = {}
        entity_seen: set[str] = set()

        for operation in plan.operations:
            ready, dependency_error = cls._operation_is_ready(
                operation,
                completed,
            )

            if not ready:
                skipped = QueryExecutionRecord(
                    operation_id=operation.operation_id,
                    tool_name=operation.tool_name,
                    capability=operation.capability,
                    success=False,
                    skipped=True,
                    answer=(
                        "Operation skipped because a required upstream "
                        "operation did not complete."
                    ),
                    limitations=[
                        dependency_error or "DEPENDENCY_NOT_READY"
                    ],
                    depends_on=list(operation.depends_on),
                )

                result.records.append(skipped)
                result.skipped_operations.append(operation.operation_id)
                completed[operation.operation_id] = skipped
                continue

            entities = cls._entity_candidates(
                operation=operation,
                plan=plan,
            )

            operation_records: List[QueryExecutionRecord] = []

            for entity in entities:
                record = cls._execute_one(
                    plan=plan,
                    operation=operation,
                    entity=entity,
                    db=db,
                    tenant_id=tenant_id,
                )

                operation_records.append(record)
                result.records.append(record)

                if entity and entity.entity_id:
                    normalized = entity.entity_id.upper()
                    if normalized not in entity_seen:
                        entity_seen.add(normalized)
                        result.entities_executed.append(normalized)

            # An operation is considered successful only if every required
            # concrete execution succeeded.
            if operation_records and all(
                record.success for record in operation_records
            ):
                successful_record = operation_records[0]
                completed[operation.operation_id] = successful_record
                result.successful_operations.append(operation.operation_id)
            else:
                failed_record = operation_records[0] if operation_records else None

                if failed_record is not None:
                    completed[operation.operation_id] = failed_record

                result.failed_operations.append(operation.operation_id)

        # Consolidate evidence.
        for record in result.records:
            if record.skipped:
                continue

            result.evidence.append(
                {
                    "operation_id": record.operation_id,
                    "tool_name": record.tool_name,
                    "capability": record.capability,
                    "entity_id": record.entity_id,
                    "success": record.success,
                    "answer": record.answer,
                    "data": record.data,
                    "limitations": record.limitations,
                    "provenance": record.provenance,
                }
            )

            for limitation in record.limitations:
                if limitation not in result.limitations:
                    result.limitations.append(limitation)

        result.data = {
            "operation_results": [
                record.model_dump()
                for record in result.records
                if not record.skipped
            ],
        }

        required_operation_ids = [
            operation.operation_id
            for operation in plan.operations
            if operation.required
        ]

        result.success = bool(required_operation_ids) and all(
            operation_id in result.successful_operations
            for operation_id in required_operation_ids
        )

        if not plan.operations:
            result.success = False
            result.limitations.append("NO_DETERMINISTIC_OPERATIONS")

        if plan.missing_requirements:
            result.success = False
            result.limitations.extend(
                requirement
                for requirement in plan.missing_requirements
                if requirement not in result.limitations
            )

        result.provenance.update(
            {
                "successful_operation_count": len(
                    result.successful_operations
                ),
                "failed_operation_count": len(
                    result.failed_operations
                ),
                "skipped_operation_count": len(
                    result.skipped_operations
                ),
                "entities_executed": list(result.entities_executed),
                "deterministic_success": result.success,
            }
        )

        return result
