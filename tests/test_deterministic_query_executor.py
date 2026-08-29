from aurix_core.intelligence.query_executor import DeterministicQueryExecutor
from aurix_core.intelligence.query_plan import (
    DeterministicOperation,
    DeterministicQueryPlan,
    QueryEntity,
    QueryIntent,
)


def test_executor_plan_supports_multiple_entities():
    plan = DeterministicQueryPlan(
        query="Compare supplier SUP-101 and SUP-202 on OTIF.",
        normalized_query="compare supplier sup-101 and sup-202 on otif",
        intent=QueryIntent.COMPARE,
        confidence=0.99,
        entities=[
            QueryEntity(
                entity_type="supplier",
                entity_id="SUP-101",
                confidence=0.99,
            ),
            QueryEntity(
                entity_type="supplier",
                entity_id="SUP-202",
                confidence=0.99,
            ),
        ],
        operations=[
            DeterministicOperation(
                operation_id="OP-1",
                tool_name="supplier.performance",
                capability="SUPPLIER_PERFORMANCE_RISK",
            )
        ],
    )

    assert len(plan.entities) == 2
    assert len(plan.operations) == 1


def test_executor_without_operations_does_not_claim_success():
    plan = DeterministicQueryPlan(
        query="test",
        normalized_query="test",
        intent=QueryIntent.READ,
        confidence=1.0,
    )

    result = DeterministicQueryExecutor.execute(
        plan=plan,
        db=None,
        tenant_id="TEST",
    )

    assert result.success is False
    assert "NO_DETERMINISTIC_OPERATIONS" in result.limitations
