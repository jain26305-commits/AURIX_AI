"""
AURIX Enterprise Agent Studio — Visual Workflow Engine
Phase 30 Core Implementation.
Manages DAG workflow graph composition, node/edge connections, and graph structure validation.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set
from sqlalchemy.orm import Session
from aurix_core.studio.contracts import (
    NodeType,
    StudioAgentStatus,
    StudioWorkflowDefinition,
    WorkflowEdge,
    WorkflowNode,
    WorkflowTrigger,
)


class WorkflowBuilder:
    """Visual DAG workflow graph composition and integrity manager."""

    _workflows: Dict[str, StudioWorkflowDefinition] = {}

    @classmethod
    def create_workflow(
        cls,
        workflow: StudioWorkflowDefinition,
        db: Optional[Session] = None,
    ) -> StudioWorkflowDefinition:
        """Create or initialize a visual workflow definition."""
        cls._workflows[workflow.workflow_id] = workflow
        if db is not None:
            try:
                from aurix_core.database.models.studio import StudioWorkflowModel
                rec = db.query(StudioWorkflowModel).filter(StudioWorkflowModel.id == workflow.workflow_id).first()
                if not rec:
                    rec = StudioWorkflowModel(
                        id=workflow.workflow_id,
                        tenant_id=workflow.tenant_id,
                        name=workflow.name,
                        description=workflow.description,
                        version=workflow.version,
                        status=workflow.status.value,
                        triggers_json=[t.model_dump() for t in workflow.triggers],
                        nodes_json=[n.model_dump() for n in workflow.nodes],
                        edges_json=[e.model_dump() for e in workflow.edges],
                    )
                    db.add(rec)
                    db.commit()
            except Exception:
                db.rollback()
        return workflow

    @classmethod
    def get_workflow(cls, workflow_id: str, db: Optional[Session] = None) -> Optional[StudioWorkflowDefinition]:
        """Retrieve workflow definition from DB or cache."""
        if workflow_id in cls._workflows:
            return cls._workflows[workflow_id]
        if db is not None:
            from aurix_core.database.models.studio import StudioWorkflowModel
            rec = db.query(StudioWorkflowModel).filter(StudioWorkflowModel.id == workflow_id).first()
            if rec:
                wfl = StudioWorkflowDefinition(
                    workflow_id=rec.id,
                    tenant_id=rec.tenant_id,
                    name=rec.name,
                    description=rec.description,
                    version=rec.version,
                    status=StudioAgentStatus(rec.status),
                    triggers=[WorkflowTrigger(**t) for t in (rec.triggers_json or [])],
                    nodes=[WorkflowNode(**n) for n in (rec.nodes_json or [])],
                    edges=[WorkflowEdge(**e) for e in (rec.edges_json or [])],
                )
                cls._workflows[rec.id] = wfl
                return wfl
        return None

    @classmethod
    def detect_cycles(cls, workflow: StudioWorkflowDefinition) -> bool:
        """DFS cycle detection ensuring workflow graph is a valid Directed Acyclic Graph (DAG)."""
        adjacency: Dict[str, List[str]] = {n.node_id: [] for n in workflow.nodes}
        for edge in workflow.edges:
            if edge.source_node_id in adjacency:
                adjacency[edge.source_node_id].append(edge.target_node_id)

        visited: Set[str] = set()
        rec_stack: Set[str] = set()

        def _dfs(node_id: str) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)
            for neighbor in adjacency.get(node_id, []):
                if neighbor not in visited:
                    if _dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            rec_stack.remove(node_id)
            return False

        for n in workflow.nodes:
            if n.node_id not in visited:
                if _dfs(n.node_id):
                    return True
        return False
