"""
AURIX Risk, Causal & External Intelligence — Risk Propagation Engine
Phase 26 Core Implementation.
Traverses cross-domain risk pathways via Phase 24 Context Graph (Supplier -> Material -> Mfg -> Customer -> Cash).
"""

from __future__ import annotations

from typing import Any, Dict, List, Set


class RiskPropagationEngine:
    """Traverses downstream operational consequences starting from a root risk finding."""

    @classmethod
    def propagate_risk(
        cls,
        root_entity_id: str,
        edges: List[Dict[str, Any]],
        nodes_lookup: Dict[str, Dict[str, Any]],
        max_hops: int = 4,
    ) -> Dict[str, Any]:
        """
        Traverse risk consequences across Context Graph relationships cycle-safely.
        """
        # Build adjacency
        adj: Dict[str, List[str]] = {}
        for edge in edges:
            u = str(edge.get("source_node_id"))
            v = str(edge.get("target_node_id"))
            adj.setdefault(u, []).append(v)
            adj.setdefault(v, []).append(u)

        visited: Set[str] = {root_entity_id}
        queue = [root_entity_id]
        propagation_path: List[Dict[str, Any]] = []
        total_revenue_exposed = 0.0

        for hop in range(max_hops):
            next_queue = []
            for curr in queue:
                for neighbor in adj.get(curr, []):
                    if neighbor not in visited:
                        visited.add(neighbor)
                        next_queue.append(neighbor)

                        node = nodes_lookup.get(neighbor, {})
                        node_type = str(node.get("entity_type") or "UNKNOWN")
                        name = str(node.get("name") or neighbor)
                        amt = float(node.get("attributes", {}).get("total_amount") or 0.0)
                        total_revenue_exposed += amt

                        propagation_path.append({
                            "hop": hop + 1,
                            "entity_id": neighbor,
                            "entity_name": name,
                            "entity_type": node_type,
                            "financial_exposure_usd": amt,
                        })
            queue = next_queue

        return {
            "root_risk_entity": root_entity_id,
            "total_downstream_entities_affected": len(propagation_path),
            "total_revenue_exposed_usd": round(total_revenue_exposed, 2),
            "propagation_path": propagation_path,
        }
