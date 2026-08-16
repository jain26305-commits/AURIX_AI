"""Repository implementations for Phase 7A Network Flow entities."""

import json
from typing import Any, Dict, List, Optional, Type, cast
from sqlalchemy.orm import Session

from aurix_core.database.models.network import (
    NetworkEdgeSnapshot,
    NetworkFlowRun,
    NetworkNodeSnapshot,
    NetworkOptimizationRun,
    NetworkRiskSnapshot,
)
from aurix_core.database.repositories.base import BaseRepository


def _extract_id_str(val: Any) -> Optional[str]:
    """Safely extracts a string ID from string, ORM instance, or dictionary."""
    if val is None:
        return None
    if isinstance(val, str):
        s = val.strip()
        return s if s else None
    if hasattr(val, "id") and getattr(val, "id"):
        return str(getattr(val, "id"))
    if hasattr(val, "run_id") and getattr(val, "run_id"):
        return str(getattr(val, "run_id"))
    if hasattr(val, "node_id") and getattr(val, "node_id"):
        return str(getattr(val, "node_id"))
    if hasattr(val, "edge_id") and getattr(val, "edge_id"):
        return str(getattr(val, "edge_id"))
    if hasattr(val, "risk_id") and getattr(val, "risk_id"):
        return str(getattr(val, "risk_id"))
    if isinstance(val, dict):
        for k in ("run_id", "network_run_id", "flow_run_id", "intelligence_run_id", "id", "node_id", "edge_id", "risk_id"):
            if k in val and val[k]:
                return str(val[k])
    return str(val)


def _init_repo(repo: BaseRepository[Any], model_cls: Type[Any], *args: Any, **kwargs: Any) -> None:
    """Safely initializes BaseRepository regardless of 2-arg or 3-arg call convention."""
    db_val: Optional[Session] = kwargs.get("db")
    tenant_val: Optional[str] = kwargs.get("tenant_id")

    positional = list(args)
    if positional:
        if isinstance(positional[0], type):
            positional.pop(0)
        if len(positional) >= 1 and isinstance(positional[0], Session):
            db_val = positional[0]
        if len(positional) >= 2 and isinstance(positional[1], str):
            tenant_val = positional[1]

    if db_val is None or tenant_val is None:
        for arg in args:
            if isinstance(arg, Session) or hasattr(arg, "query"):
                db_val = arg
            elif isinstance(arg, str):
                tenant_val = arg

    if db_val is None or tenant_val is None:
        raise ValueError("Database session and tenant_id are required to initialize repository.")

    BaseRepository.__init__(repo, model_cls, db_val, tenant_val)


class NetworkFlowRunRepository(BaseRepository[NetworkFlowRun]):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        _init_repo(self, NetworkFlowRun, *args, **kwargs)

    def get_by_hash(self, dataset_hash: str) -> Optional[NetworkFlowRun]:
        return self.db.query(NetworkFlowRun).filter(
            NetworkFlowRun.tenant_id == self.tenant_id,
            NetworkFlowRun.dataset_hash == dataset_hash,
        ).first()

    def get_by_run_id(self, run_id: Optional[Any] = None) -> Optional[NetworkFlowRun]:
        """Return only the explicitly requested tenant-scoped run.

        A missing run ID is not a valid request for a specific run and must
        never silently resolve to the latest run. This prevents cross-run
        contamination and makes missing identifiers fail closed.
        """
        id_str = _extract_id_str(run_id)
        if not id_str or id_str == "None":
            return None

        return self.db.query(NetworkFlowRun).filter(
            NetworkFlowRun.tenant_id == self.tenant_id,
            (NetworkFlowRun.id == id_str) | (NetworkFlowRun.run_id == id_str),
        ).first()

    def get_by_id(self, id: Any) -> Optional[NetworkFlowRun]:
        id_str = _extract_id_str(id)
        if id_str and id_str != "None":
            return self.db.query(NetworkFlowRun).filter(
                NetworkFlowRun.tenant_id == self.tenant_id,
                (NetworkFlowRun.id == id_str) | (NetworkFlowRun.run_id == id_str),
            ).first()
        return None

    def get(self, id: Any) -> Optional[NetworkFlowRun]:
        return self.get_by_id(id)

    def get_latest_run(self) -> Optional[NetworkFlowRun]:
        return self.db.query(NetworkFlowRun).filter(
            NetworkFlowRun.tenant_id == self.tenant_id,
        ).order_by(NetworkFlowRun.created_at.desc()).first()

    def get_provenance(self, run_id: Optional[Any] = None) -> Optional[Dict[str, Any]]:
        run = self.get_by_run_id(run_id)
        if not run or not run.provenance:
            return None
        try:
            raw_prov = str(getattr(run, "provenance", "{}") or "{}")
            parsed = json.loads(raw_prov)
            return cast(Dict[str, Any], parsed) if isinstance(parsed, dict) else {"raw": raw_prov}
        except Exception:
            return {"raw": str(getattr(run, "provenance", "{}"))}


NetworkIntelligenceRunRepository = NetworkFlowRunRepository


class NetworkNodeSnapshotRepository(BaseRepository[NetworkNodeSnapshot]):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        _init_repo(self, NetworkNodeSnapshot, *args, **kwargs)

    def get_by_run_id(self, run_id: Optional[Any] = None) -> List[NetworkNodeSnapshot]:
        id_str = _extract_id_str(run_id)
        query = self.db.query(NetworkNodeSnapshot).filter(
            NetworkNodeSnapshot.tenant_id == self.tenant_id
        )
        if id_str and id_str != "None":
            query = query.filter(
                (NetworkNodeSnapshot.run_id == id_str) | (NetworkNodeSnapshot.id == id_str)
            )
        return query.all()

    def get_nodes_by_run_id(self, run_id: Optional[Any] = None) -> List[NetworkNodeSnapshot]:
        return self.get_by_run_id(run_id)

    def find_by_run_id(self, run_id: Optional[Any] = None) -> List[NetworkNodeSnapshot]:
        return self.get_by_run_id(run_id)

    def get_by_node_id(self, node_id: Any, run_id: Optional[Any] = None) -> Optional[NetworkNodeSnapshot]:
        nid_str = _extract_id_str(node_id)
        if not nid_str:
            return None

        rid_str = _extract_id_str(run_id)
        query = self.db.query(NetworkNodeSnapshot).filter(
            NetworkNodeSnapshot.tenant_id == self.tenant_id,
            (NetworkNodeSnapshot.node_id == nid_str)
            | (NetworkNodeSnapshot.id == nid_str)
            | (NetworkNodeSnapshot.node_name == nid_str),
        )
        if rid_str and rid_str != "None":
            query = query.filter(
                (NetworkNodeSnapshot.run_id == rid_str) | (NetworkNodeSnapshot.id == rid_str)
            )
        return query.first()

    def get_node(self, node_id: Any) -> Optional[NetworkNodeSnapshot]:
        return self.get_by_node_id(node_id)

    def get_by_id(self, id: Any) -> Optional[NetworkNodeSnapshot]:
        return self.get_by_node_id(id)

    def get(self, id: Any) -> Optional[NetworkNodeSnapshot]:
        return self.get_by_node_id(id)


class NetworkEdgeSnapshotRepository(BaseRepository[NetworkEdgeSnapshot]):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        _init_repo(self, NetworkEdgeSnapshot, *args, **kwargs)

    def get_by_run_id(self, run_id: Optional[Any] = None) -> List[NetworkEdgeSnapshot]:
        id_str = _extract_id_str(run_id)
        query = self.db.query(NetworkEdgeSnapshot).filter(
            NetworkEdgeSnapshot.tenant_id == self.tenant_id
        )
        if id_str and id_str != "None":
            query = query.filter(
                (NetworkEdgeSnapshot.run_id == id_str) | (NetworkEdgeSnapshot.id == id_str)
            )
        return query.all()

    def get_edges_by_run_id(self, run_id: Optional[Any] = None) -> List[NetworkEdgeSnapshot]:
        return self.get_by_run_id(run_id)

    def find_by_run_id(self, run_id: Optional[Any] = None) -> List[NetworkEdgeSnapshot]:
        return self.get_by_run_id(run_id)

    def get_by_edge_id(self, edge_id: Any, run_id: Optional[Any] = None) -> Optional[NetworkEdgeSnapshot]:
        eid_str = _extract_id_str(edge_id)
        if not eid_str:
            return None

        rid_str = _extract_id_str(run_id)
        query = self.db.query(NetworkEdgeSnapshot).filter(
            NetworkEdgeSnapshot.tenant_id == self.tenant_id,
            (NetworkEdgeSnapshot.edge_id == eid_str) | (NetworkEdgeSnapshot.id == eid_str),
        )
        if rid_str and rid_str != "None":
            query = query.filter(
                (NetworkEdgeSnapshot.run_id == rid_str) | (NetworkEdgeSnapshot.id == rid_str)
            )
        return query.first()

    def get_edge(self, edge_id: Any) -> Optional[NetworkEdgeSnapshot]:
        return self.get_by_edge_id(edge_id)

    def get_by_id(self, id: Any) -> Optional[NetworkEdgeSnapshot]:
        return self.get_by_edge_id(id)

    def get(self, id: Any) -> Optional[NetworkEdgeSnapshot]:
        return self.get_by_edge_id(id)


class NetworkRiskSnapshotRepository(BaseRepository[NetworkRiskSnapshot]):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        _init_repo(self, NetworkRiskSnapshot, *args, **kwargs)

    def get_by_run_id(self, run_id: Optional[Any] = None) -> List[NetworkRiskSnapshot]:
        id_str = _extract_id_str(run_id)
        query = self.db.query(NetworkRiskSnapshot).filter(
            NetworkRiskSnapshot.tenant_id == self.tenant_id
        )
        if id_str and id_str != "None":
            query = query.filter(
                (NetworkRiskSnapshot.run_id == id_str) | (NetworkRiskSnapshot.id == id_str)
            )
        return query.all()

    def get_risks_by_run_id(self, run_id: Optional[Any] = None) -> List[NetworkRiskSnapshot]:
        return self.get_by_run_id(run_id)

    def find_by_run_id(self, run_id: Optional[Any] = None) -> List[NetworkRiskSnapshot]:
        return self.get_by_run_id(run_id)

    def get_by_node_id(self, node_id: Any, run_id: Optional[Any] = None) -> List[NetworkRiskSnapshot]:
        nid_str = _extract_id_str(node_id)
        rid_str = _extract_id_str(run_id)
        query = self.db.query(NetworkRiskSnapshot).filter(
            NetworkRiskSnapshot.tenant_id == self.tenant_id
        )
        if nid_str:
            query = query.filter(
                (NetworkRiskSnapshot.node_id == nid_str)
                | (NetworkRiskSnapshot.id == nid_str)
                | (NetworkRiskSnapshot.risk_id == nid_str)
            )
        if rid_str and rid_str != "None":
            query = query.filter(
                (NetworkRiskSnapshot.run_id == rid_str) | (NetworkRiskSnapshot.id == rid_str)
            )
        return query.all()

    def get_by_risk_id(self, risk_id: Any, run_id: Optional[Any] = None) -> Optional[NetworkRiskSnapshot]:
        rid_val = _extract_id_str(risk_id)
        if not rid_val:
            return None

        rid_str = _extract_id_str(run_id)
        query = self.db.query(NetworkRiskSnapshot).filter(
            NetworkRiskSnapshot.tenant_id == self.tenant_id,
            (NetworkRiskSnapshot.risk_id == rid_val)
            | (NetworkRiskSnapshot.id == rid_val)
            | (NetworkRiskSnapshot.node_id == rid_val),
        )
        if rid_str and rid_str != "None":
            query = query.filter(
                (NetworkRiskSnapshot.run_id == rid_str) | (NetworkRiskSnapshot.id == rid_str)
            )
        return query.first()

    def get_by_id(self, id: Any) -> Optional[NetworkRiskSnapshot]:
        return self.get_by_risk_id(id)

    def get(self, id: Any) -> Optional[NetworkRiskSnapshot]:
        return self.get_by_risk_id(id)


NetworkRiskEventRepository = NetworkRiskSnapshotRepository


class NetworkOptimizationRunRepository(BaseRepository[NetworkOptimizationRun]):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        _init_repo(self, NetworkOptimizationRun, *args, **kwargs)

    def get_by_run_id(self, run_id: Optional[Any] = None) -> Optional[NetworkOptimizationRun]:
        """Return only the explicitly requested tenant-scoped optimization run."""
        id_str = _extract_id_str(run_id)
        if not id_str or id_str == "None":
            return None

        return self.db.query(NetworkOptimizationRun).filter(
            NetworkOptimizationRun.tenant_id == self.tenant_id,
            (NetworkOptimizationRun.run_id == id_str) | (NetworkOptimizationRun.id == id_str),
        ).order_by(NetworkOptimizationRun.created_at.desc()).first()

    def get_by_id(self, id: Any) -> Optional[NetworkOptimizationRun]:
        return self.get_by_run_id(id)

    def get(self, id: Any) -> Optional[NetworkOptimizationRun]:
        return self.get_by_run_id(id)