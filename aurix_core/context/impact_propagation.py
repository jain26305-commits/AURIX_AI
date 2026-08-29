"""
AURIX Enterprise Business Context Graph — Impact Propagation Engine
Phase 24 Core Implementation.
Traverses upstream operational disruptions (supplier delays, machine bottlenecks) downstream to customer orders and financial risk.
"""

from __future__ import annotations

from typing import Any, Dict, List, Set
from aurix_core.context.contracts import ContextEdge, ContextNode


class ImpactPropagationEngine:
    """Traverses downstream consequences of operational disruptions."""

    @classmethod
    def propagate_disruption(
        cls,
        disrupted_node_id: str,
        nodes: Dict[str, ContextNode],
        edges: List[ContextEdge],
    ) -> Dict[str, Any]:
        """
        Traverses downstream impact starting from a root constraint (e.g. Supplier defect or WorkCenter bottleneck).
        """
        impacted_orders: List[Dict[str, Any]] = []
        impacted_customers: Set[str] = set()
        total_revenue_exposed = 0.0

        # Pre-index outward edges
        out_edges: Dict[str, List[str]] = {}
        for edge in edges:
            out_edges.setdefault(edge.source_node_id, []).append(edge.target_node_id)
            out_edges.setdefault(edge.target_node_id, []).append(edge.source_node_id)

        # Traverse 2-3 hops outward
        visited: Set[str] = {disrupted_node_id}
        queue = [disrupted_node_id]

        for _ in range(3):
            next_queue = []
            for curr in queue:
                for neighbor in out_edges.get(curr, []):
                    if neighbor not in visited:
                        visited.add(neighbor)
                        next_queue.append(neighbor)

                        node = nodes.get(neighbor)
                        if node and node.entity_type.value == "ORDER":
                            amt = float(node.attributes.get("total_amount") or 0.0)
                            total_revenue_exposed += amt
                            impacted_orders.append({"order_id": node.canonical_id, "amount": amt})
                        elif node and node.entity_type.value == "CUSTOMER":
                            impacted_customers.add(node.name)
            queue = next_queue

        return {
            "root_disrupted_node": disrupted_node_id,
            "total_nodes_impacted": len(visited),
            "impacted_orders_count": len(impacted_orders),
            "impacted_customers": list(impacted_customers),
            "total_revenue_at_risk": round(total_revenue_exposed, 2),
            "details": impacted_orders,
        }
