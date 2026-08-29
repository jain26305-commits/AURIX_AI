"""
AURIX Enterprise Business Context Graph — Graph Traversal & Why-Chain Engine
Phase 24 Core Implementation.
Executes cycle-safe N-hop graph queries, shortest path discovery, and Why-Chain causal link reconstruction.
"""

from __future__ import annotations

from collections import deque
from typing import Any, Dict, List, Optional, Set, Tuple
from aurix_core.context.contracts import (
    ContextEdge,
    ContextNode,
    RelationshipConfidence,
    WhyChainReport,
    WhyChainStep,
)


class GraphTraversalEngine:
    """Cycle-safe in-memory and persisted graph traversal query engine."""

    @classmethod
    def get_neighborhood(
        cls,
        node_id: str,
        nodes: Dict[str, ContextNode],
        edges: List[ContextEdge],
        max_hops: int = 1,
    ) -> Dict[str, Any]:
        """Retrieve 1-hop or N-hop subgraph neighborhood around an entity node."""
        visited_nodes: Set[str] = {node_id}
        result_edges: List[ContextEdge] = []
        queue: deque[Tuple[str, int]] = deque([(node_id, 0)])

        # Pre-index adjacency
        adj: Dict[str, List[ContextEdge]] = {}
        for edge in edges:
            adj.setdefault(edge.source_node_id, []).append(edge)
            adj.setdefault(edge.target_node_id, []).append(edge)

        while queue:
            curr, depth = queue.popleft()
            if depth >= max_hops:
                continue

            for edge in adj.get(curr, []):
                neighbor = edge.target_node_id if edge.source_node_id == curr else edge.source_node_id
                result_edges.append(edge)
                if neighbor not in visited_nodes:
                    visited_nodes.add(neighbor)
                    queue.append((neighbor, depth + 1))

        return {
            "center_node": nodes.get(node_id),
            "nodes": [nodes[n] for n in visited_nodes if n in nodes],
            "edges": result_edges,
            "total_nodes": len(visited_nodes),
            "total_edges": len(result_edges),
        }

    @classmethod
    def reconstruct_why_chain(
        cls,
        tenant_id: str,
        symptom_node_id: str,
        root_cause_node_id: str,
        nodes: Dict[str, ContextNode],
        edges: List[ContextEdge],
    ) -> WhyChainReport:
        """
        Reconstructs the Why-Chain linking an operational symptom to its root cause via BFS shortest path.
        """
        # BFS Shortest Path Traversal
        adj: Dict[str, List[Tuple[str, ContextEdge]]] = {}
        for edge in edges:
            adj.setdefault(edge.source_node_id, []).append((edge.target_node_id, edge))
            adj.setdefault(edge.target_node_id, []).append((edge.source_node_id, edge))

        queue: deque[List[Tuple[str, Optional[ContextEdge]]]] = deque([[(symptom_node_id, None)]])
        visited: Set[str] = {symptom_node_id}
        found_path: Optional[List[Tuple[str, Optional[ContextEdge]]]] = None

        while queue:
            path = queue.popleft()
            curr_node, _ = path[-1]

            if curr_node == root_cause_node_id:
                found_path = path
                break

            for neighbor, edge in adj.get(curr_node, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    new_path = list(path)
                    new_path.append((neighbor, edge))
                    queue.append(new_path)

        steps: List[WhyChainStep] = []
        if found_path and len(found_path) > 1:
            for idx in range(len(found_path) - 1):
                u_id, _ = found_path[idx]
                v_id, edge = found_path[idx + 1]
                u_node = nodes.get(u_id)
                v_node = nodes.get(v_id)

                steps.append(
                    WhyChainStep(
                        step_index=idx + 1,
                        from_node_name=u_node.name if u_node else u_id,
                        from_node_type=u_node.entity_type.value if u_node else "UNKNOWN",
                        to_node_name=v_node.name if v_node else v_id,
                        to_node_type=v_node.entity_type.value if v_node else "UNKNOWN",
                        relationship_type=edge.relationship_type.value if edge else "LINKED_TO",
                        confidence=edge.confidence_level if edge else RelationshipConfidence.OBSERVED,
                        evidence_summary=f"Traversed edge {u_id} -> {v_id}",
                    )
                )

        target_name = nodes.get(symptom_node_id).name if symptom_node_id in nodes else symptom_node_id
        root_name = nodes.get(root_cause_node_id).name if root_cause_node_id in nodes else root_cause_node_id

        return WhyChainReport(
            tenant_id=tenant_id,
            target_symptom=target_name,
            root_cause_candidate=root_name,
            confidence_pct=95.0 if steps else 0.0,
            chain_length=len(steps),
            steps=steps,
        )
