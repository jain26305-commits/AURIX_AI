"""Enterprise transactional service adapter for Phase 7 Network Intelligence."""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, cast

from sqlalchemy.orm import Session

from aurix_core.database.models.network import (
    NetworkEdgeSnapshot,
    NetworkFlowRun,
    NetworkNodeSnapshot,
    NetworkOptimizationRun,
    NetworkRiskSnapshot,
)
from aurix_core.database.repositories.network import (
    NetworkEdgeSnapshotRepository,
    NetworkFlowRunRepository,
    NetworkNodeSnapshotRepository,
    NetworkOptimizationRunRepository,
    NetworkRiskSnapshotRepository,
)
from aurix_core.network.config import NetworkConfiguration
from aurix_core.network.orchestrator import Phase7AOrchestrator


def _json_dumps(value: Any) -> str:
    """Serialize a Python value into stable JSON for persistence."""
    return json.dumps(value, default=str, sort_keys=True)


def _model_dump(value: Any) -> Any:
    """Convert Pydantic/ORM-like objects into serializable values."""
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if hasattr(value, "dict"):
        return value.dict()
    return value


def _as_dict(value: Any) -> Dict[str, Any]:
    """Safely convert an object into a dictionary."""
    dumped = _model_dump(value)
    return dumped if isinstance(dumped, dict) else {}


def _safe_float(val: Any, default: float = 0.0) -> float:
    """Safely convert scalar or dictionary metrics to float."""
    if val is None:
        return default

    if isinstance(val, (int, float)):
        return float(val)

    if isinstance(val, str):
        try:
            return float(val.strip())
        except (ValueError, TypeError):
            return default

    if isinstance(val, dict):
        for key in (
            "value",
            "val",
            "rate",
            "cost",
            "amount",
            "capacity",
            "holding_cost_rate",
        ):
            if key in val:
                return _safe_float(val[key], default)

    return default


def _optional_float(val: Any) -> Optional[float]:
    """Return None when a numeric business fact is absent or invalid."""
    if val is None:
        return None

    if isinstance(val, (int, float)):
        return float(val)

    if isinstance(val, str):
        try:
            return float(val.strip())
        except (ValueError, TypeError):
            return None

    if isinstance(val, dict):
        for key in (
            "value",
            "val",
            "rate",
            "cost",
            "amount",
            "capacity",
            "holding_cost_rate",
            "probability",
            "risk_score",
        ):
            if key in val:
                return _optional_float(val[key])

    return None


def _safe_int(val: Any, default: int = 0) -> int:
    """Safely convert scalar or dictionary metrics to int."""
    if val is None:
        return default

    if isinstance(val, int):
        return val

    if isinstance(val, float):
        return int(val)

    if isinstance(val, str):
        try:
            return int(float(val.strip()))
        except (ValueError, TypeError):
            return default

    if isinstance(val, dict):
        for key in ("value", "val", "level", "tier", "tier_level"):
            if key in val:
                return _safe_int(val[key], default)

    return default


def _optional_int(val: Any) -> Optional[int]:
    """Return None when an integer business fact is absent or invalid."""
    if val is None:
        return None

    if isinstance(val, int):
        return val

    if isinstance(val, float):
        return int(val)

    if isinstance(val, str):
        try:
            return int(float(val.strip()))
        except (ValueError, TypeError):
            return None

    if isinstance(val, dict):
        for key in ("value", "val", "level", "tier", "tier_level"):
            if key in val:
                return _optional_int(val[key])

    return None


class NetworkIntelligenceService:

    """
    Enterprise service for Phase 7 Network Intelligence.

    Responsibilities:
        - tenant-scoped idempotency
        - Phase 7A orchestration
        - persistence of authoritative analytical results
        - transaction handling
        - provenance preservation
    """

    def __init__(
        self,
        db: Session,
        tenant_id: str,
    ) -> None:
        self.db = db
        self.tenant_id = tenant_id

        self.run_repo = NetworkFlowRunRepository(db, tenant_id)
        self.flow_run_repo = self.run_repo
        self.node_repo = NetworkNodeSnapshotRepository(db, tenant_id)
        self.edge_repo = NetworkEdgeSnapshotRepository(db, tenant_id)
        self.risk_repo = NetworkRiskSnapshotRepository(db, tenant_id)
        self.opt_repo = NetworkOptimizationRunRepository(db, tenant_id)
        self._persistence_limitations: List[str] = []

    @staticmethod
    def _compute_dataset_hash(
        payload: Dict[str, Any],
        config: Dict[str, Any],
    ) -> str:
        """Compute canonical SHA-256 dataset/configuration hash."""
        canonical_payload = {
            "payload": payload,
            "config": config,
        }

        canonical_json = json.dumps(
            canonical_payload,
            sort_keys=True,
            default=str,
            separators=(",", ":"),
        )

        return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()

    def _build_run(
        self,
        run_id: str,
        dataset_hash: str,
        config: Dict[str, Any],
        started_at: datetime,
    ) -> NetworkFlowRun:
        """Create the execution run record."""
        return NetworkFlowRun(
            id=run_id,
            run_id=run_id,
            tenant_id=self.tenant_id,
            dataset_hash=dataset_hash,
            status="EXECUTING",
            configuration=_json_dumps(config),
            provenance=_json_dumps(
                {
                    "run_id": run_id,
                    "tenant_id": self.tenant_id,
                    "dataset_hash": dataset_hash,
                    "phase": "PHASE_7A",
                    "pipeline_version": "7.0.0",
                    "started_at": started_at.isoformat(),
                }
            ),
            created_at=started_at,
        )

    def _persist_nodes(
        self,
        run_id: str,
        contract: Dict[str, Any],
    ) -> int:
        """Persist only node records with complete required persistence facts."""
        nodes_raw = contract.get("nodes", {})

        if isinstance(nodes_raw, dict):
            node_items = list(nodes_raw.items())
        elif isinstance(nodes_raw, list):
            node_items = [
                (
                    _as_dict(node).get("node_id")
                    or _as_dict(node).get("id"),
                    node,
                )
                for node in nodes_raw
            ]
        else:
            return 0

        count = 0

        for raw_node_id, raw_node in node_items:
            node = _as_dict(raw_node)
            node_id = str(raw_node_id or "").strip()

            if not node_id:
                self._persistence_limitations.append(
                    "Skipped network node because node_id is missing."
                )
                continue

            node_name_value = node.get("node_name") or node.get("name")
            node_type_value = node.get("node_type")
            location_value = node.get("location_name") or node.get("location")
            tier_level = _optional_int(
                node.get("tier_level")
                if node.get("tier_level") is not None
                else node.get("tier")
            )
            holding_cost = _optional_float(
                node.get("holding_cost_rate")
                if node.get("holding_cost_rate") is not None
                else node.get("holding_cost")
            )
            capacity = _optional_float(node.get("capacity"))

            required_missing = []
            if node_name_value in (None, ""):
                required_missing.append("node_name")
            if node_type_value in (None, ""):
                required_missing.append("node_type")

            if required_missing:
                self._persistence_limitations.append(
                    f"Skipped node '{node_id}' because required facts are missing: "
                    f"{', '.join(required_missing)}."
                )
                continue

            node_type = str(
                getattr(
                    node_type_value,
                    "value",
                    node_type_value,
                )
            )

            self.db.add(
                NetworkNodeSnapshot(
                    id=f"NODE-{uuid.uuid4().hex[:12].upper()}",
                    tenant_id=self.tenant_id,
                    run_id=run_id,
                    node_id=node_id,
                    node_name=str(node_name_value),
                    node_type=node_type,
                    location_name=(
                        str(location_value)
                        if location_value is not None
                        else None
                    ),
                    tier_level=tier_level,
                    holding_cost_rate=holding_cost,
                    capacity=capacity,
                    status="ACTIVE",
                    attributes_json=_json_dumps(node),
                    created_at=datetime.now(timezone.utc),
                )
            )
            count += 1

        return count

    def _persist_edges(
        self,
        run_id: str,
        contract: Dict[str, Any],
    ) -> int:
        """Persist only edge records with complete required persistence facts."""
        edges_raw = contract.get("edges", [])

        if isinstance(edges_raw, dict):
            edge_list = list(edges_raw.values())
        elif isinstance(edges_raw, list):
            edge_list = edges_raw
        else:
            return 0

        count = 0

        for raw_edge in edge_list:
            edge = _as_dict(raw_edge)

            source_id = (
                edge.get("source_node_id")
                or edge.get("source")
                or edge.get("from_node")
            )
            destination_id = (
                edge.get("destination_node_id")
                or edge.get("destination")
                or edge.get("to_node")
            )
            sku_id = edge.get("sku_id") or edge.get("sku")
            if sku_id in (None, ""):
                self._persistence_limitations.append(
                    "Skipped network edge because sku_id is missing."
                )
                continue

            supplied_edge_id = edge.get("edge_id") or edge.get("id")
            edge_id = (
                str(supplied_edge_id)
                if supplied_edge_id not in (None, "")
                else f"{source_id}->{destination_id}:{sku_id}"
            )

            transport_value = edge.get("transport_mode")
            lead_time = _optional_float(
                edge.get("nominal_lead_time_days")
                if edge.get("nominal_lead_time_days") is not None
                else edge.get("lead_time_days")
                if edge.get("lead_time_days") is not None
                else edge.get("lead_time")
            )
            cost = _optional_float(
                edge.get("unit_transport_cost")
                if edge.get("unit_transport_cost") is not None
                else edge.get("transport_cost")
                if edge.get("transport_cost") is not None
                else edge.get("cost")
            )
            capacity = _optional_float(edge.get("capacity"))

            required_missing = []
            if source_id in (None, ""):
                required_missing.append("source_node_id")
            if destination_id in (None, ""):
                required_missing.append("destination_node_id")
            if sku_id in (None, ""):
                required_missing.append("sku_id")
            if edge_id in (None, ""):
                required_missing.append("edge_id")

            if required_missing:
                self._persistence_limitations.append(
                    "Skipped network edge because required facts are missing: "
                    f"{', '.join(required_missing)}."
                )
                continue

            transport_mode = (
                str(
                    getattr(
                        transport_value,
                        "value",
                        transport_value,
                    )
                )
                if transport_value is not None
                else None
            )

            self.db.add(
                NetworkEdgeSnapshot(
                    id=f"EDGE-{uuid.uuid4().hex[:12].upper()}",
                    tenant_id=self.tenant_id,
                    run_id=run_id,
                    edge_id=str(edge_id),
                    sku_id=str(sku_id),
                    source_node_id=str(source_id),
                    destination_node_id=str(destination_id),
                    transport_mode=transport_mode,
                    nominal_lead_time_days=lead_time,
                    unit_transport_cost=cost,
                    capacity=capacity,
                    status="ACTIVE",
                    attributes_json=_json_dumps(edge),
                    created_at=datetime.now(timezone.utc),
                )
            )
            count += 1

        return count

    def _persist_risks(
        self,
        run_id: str,
        contract: Dict[str, Any],
    ) -> int:
        """
        Persist the actual Phase 7A vulnerability indicators.

        ``NetworkRiskAnalyzer`` returns ``VulnerabilitySummary.risk_indicators``
        as NetworkRiskIndicator enum values. They are analytical findings, not
        dictionary-shaped records, so they must be normalized explicitly rather
        than passed through ``_as_dict``.
        """
        vulnerabilities = _as_dict(contract.get("vulnerabilities", {}))

        raw_indicators = vulnerabilities.get("risk_indicators", [])

        if not isinstance(raw_indicators, (list, tuple, set)):
            return 0

        # Extract concrete affected entities from the real analyzer output.
        # These are only used when the analyzer supplied actual relationships.
        single_source_dependencies = vulnerabilities.get(
            "single_source_dependencies",
            [],
        )
        single_node_dependencies = vulnerabilities.get(
            "single_node_dependencies",
            [],
        )
        high_flow_bottlenecks = vulnerabilities.get(
            "high_flow_bottlenecks",
            [],
        )

        indicator_rows: List[Dict[str, Any]] = []

        for raw_indicator in raw_indicators:
            indicator_value = getattr(
                raw_indicator,
                "value",
                raw_indicator,
            )
            indicator_name = str(indicator_value).strip()

            if not indicator_name:
                continue

            affected_node_id: Optional[str] = None
            evidence: Dict[str, Any] = {}

            if (
                indicator_name == "SINGLE_SOURCE_DEPENDENCY"
                and isinstance(single_source_dependencies, list)
                and single_source_dependencies
            ):
                evidence["finding"] = single_source_dependencies[0]

            elif (
                indicator_name == "SINGLE_NODE_DEPENDENCY"
                and isinstance(single_node_dependencies, list)
                and single_node_dependencies
            ):
                evidence["finding"] = single_node_dependencies[0]

            elif (
                indicator_name == "CAPACITY_CONSTRAINED"
                and isinstance(high_flow_bottlenecks, list)
                and high_flow_bottlenecks
            ):
                evidence["finding"] = high_flow_bottlenecks[0]

            indicator_rows.append(
                {
                    "risk_id": indicator_name,
                    "node_id": affected_node_id,
                    "severity": (
                        "HIGH"
                        if indicator_name in {
                            "SINGLE_SOURCE_DEPENDENCY",
                            "SINGLE_NODE_DEPENDENCY",
                            "CAPACITY_CONSTRAINED",
                        }
                        else None
                    ),
                    "evidence": evidence,
                }
            )

        count = 0

        for row in indicator_rows:
            self.db.add(
                NetworkRiskSnapshot(
                    id=f"RISK-{uuid.uuid4().hex[:12].upper()}",
                    risk_id=row["risk_id"],
                    tenant_id=self.tenant_id,
                    run_id=run_id,
                    node_id=row["node_id"],
                    disruption_probability=None,
                    bottleneck_severity=row["severity"],
                    estimated_days_to_recover=None,
                    risk_score=None,
                    mitigation_strategy=None,
                    evidence_json=_json_dumps(
                        {
                            "risk_indicator": row["risk_id"],
                            **row["evidence"],
                        }
                    ),
                    created_at=datetime.now(timezone.utc),
                )
            )
            count += 1

        return count

    def run_network_intelligence(


        self,
        payload: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute Phase 7A and persist the authoritative result.

        The service strictly persists analytical outputs and never fabricates
        unsupported synthetic entities.
        """
        cfg_dict = config or {}
        if not isinstance(cfg_dict, dict):
            cfg_dict = {}

        self._persistence_limitations = []

        if not isinstance(payload, dict):
            raise TypeError("Phase 7A network payload must be a dictionary.")

        dataset_hash = self._compute_dataset_hash(payload, cfg_dict)

        # --------------------------------------------------------
        # 1. Tenant-scoped idempotency lookup
        # --------------------------------------------------------
        existing_run = self.run_repo.get_by_hash(dataset_hash)

        if existing_run is not None and getattr(existing_run, "status", None) == "COMPLETED":
            provenance: Dict[str, Any] = {}
            if existing_run.provenance:
                try:
                    parsed = json.loads(str(existing_run.provenance))
                    if isinstance(parsed, dict):
                        provenance = parsed
                except (TypeError, ValueError):
                    provenance = {}

            existing_run_id = str(getattr(existing_run, "id"))
            nodes_count = int(getattr(existing_run, "node_count", len(self.get_nodes(existing_run_id))))
            edges_count = int(getattr(existing_run, "edge_count", len(self.get_edges(existing_run_id))))
            risks_count = int(getattr(existing_run, "risk_count", len(self.get_risks(existing_run_id))))

            return {
                "status": "COMPLETED",
                "idempotent_hit": True,
                "network_run_id": existing_run_id,
                "run_id": existing_run_id,
                "dataset_hash": dataset_hash,
                "node_count": nodes_count,
                "edge_count": edges_count,
                "risk_event_count": risks_count,
                "provenance": provenance,
            }

        # --------------------------------------------------------
        # 2. Create execution run
        # --------------------------------------------------------
        run_id = f"RUN-NET-{uuid.uuid4().hex[:12].upper()}"
        started_at = datetime.now(timezone.utc)

        run_rec: Any = self._build_run(
            run_id=run_id,
            dataset_hash=dataset_hash,
            config=cfg_dict,
            started_at=started_at,
        )

        self.db.add(run_rec)
        self.db.flush()

        try:
            # ----------------------------------------------------
            # 3. Execute the Phase 7A analytical engine
            # ----------------------------------------------------
            network_config = NetworkConfiguration(cfg_dict)

            orchestrator = Phase7AOrchestrator(
                network_data=payload,
                config_override=network_config,
            )

            contract_obj = orchestrator.process_network()
            contract = _as_dict(contract_obj)
            contract_status = contract.get("status", "COMPUTABLE")

            if contract_status != "COMPUTABLE":
                missing_inputs = contract.get("missing_inputs", [])
                run_rec.status = "WAITING_FOR_INPUT" if missing_inputs else "PARTIAL_SUCCESS"
                run_rec.provenance = _json_dumps(
                    {
                        "run_id": run_id,
                        "tenant_id": self.tenant_id,
                        "dataset_hash": dataset_hash,
                        "phase": "PHASE_7A",
                        "pipeline_version": "7.0.0",
                        "contract_status": contract_status,
                        "missing_inputs": missing_inputs,
                        "limitations": contract.get("limitations", []),
                    }
                )
                self.db.commit()

                return {
                    "status": run_rec.status,
                    "idempotent_hit": False,
                    "network_run_id": run_id,
                    "run_id": run_id,
                    "dataset_hash": dataset_hash,
                    "contract": contract,
                    "missing_inputs": missing_inputs,
                    "limitations": contract.get("limitations", []),
                }

            # ----------------------------------------------------
            # 4. Persist authoritative analytical outputs
            # ----------------------------------------------------
            node_count = self._persist_nodes(run_id, contract)
            edge_count = self._persist_edges(run_id, contract)
            risk_count = self._persist_risks(run_id, contract)

            completed_at = datetime.now(timezone.utc)
            duration_ms = (completed_at - started_at).total_seconds() * 1000.0

            provenance = {
                "run_id": run_id,
                "tenant_id": self.tenant_id,
                "dataset_hash": dataset_hash,
                "phase": "PHASE_7A",
                "pipeline_version": "7.0.0",
                "started_at": started_at.isoformat(),
                "completed_at": completed_at.isoformat(),
                "node_count": node_count,
                "edge_count": edge_count,
                "risk_event_count": risk_count,
                "contract_provenance": contract.get("provenance", {}),
                "limitations": contract.get("limitations", []),
            }

            run_rec.status = "COMPLETED"
            run_rec.node_count = node_count
            run_rec.edge_count = edge_count
            run_rec.risk_count = risk_count
            run_rec.duration_ms = duration_ms
            run_rec.completed_at = completed_at
            run_rec.updated_at = completed_at
            run_rec.provenance = _json_dumps(provenance)

            # Persist optimization output only when the analytical contract
            # actually supplies an objective value. Never fabricate 0.0 as a
            # business result merely because the field is absent.
            optimization_run_id: Optional[str] = None
            objective_value = _optional_float(contract.get("objective_value"))

            if objective_value is not None:
                optimization_run_id = (
                    f"OPT-{uuid.uuid4().hex[:12].upper()}"
                )
                opt_rec = NetworkOptimizationRun(
                    id=optimization_run_id,
                    tenant_id=self.tenant_id,
                    run_id=run_id,
                    status="COMPLETED",
                    objective_value=objective_value,
                    results_json=_json_dumps(contract),
                    provenance=_json_dumps(provenance),
                    completed_at=completed_at,
                    created_at=completed_at,
                )
                self.db.add(opt_rec)

            if self._persistence_limitations:
                provenance["limitations"] = [
                    *provenance.get("limitations", []),
                    *self._persistence_limitations,
                ]

            run_rec.provenance = _json_dumps(provenance)

            self.db.flush()
            self.db.commit()

            return {
                "status": run_rec.status,
                "idempotent_hit": False,
                "network_run_id": run_id,
                "run_id": run_id,
                "flow_run_id": run_id,
                "dataset_hash": dataset_hash,
                "node_count": node_count,
                "edge_count": edge_count,
                "risk_event_count": risk_count,
                "optimization_run_id": optimization_run_id,
                "contract": contract,
                "provenance": provenance,
                "limitations": provenance.get("limitations", []),
            }

        except Exception as exc:
            self.db.rollback()
            failed_run = NetworkFlowRun(
                id=run_id,
                run_id=run_id,
                tenant_id=self.tenant_id,
                dataset_hash=dataset_hash,
                status="FAILED",
                configuration=_json_dumps(cfg_dict),
                provenance=_json_dumps(
                    {
                        "run_id": run_id,
                        "tenant_id": self.tenant_id,
                        "dataset_hash": dataset_hash,
                        "phase": "PHASE_7A",
                        "error": str(exc),
                    }
                ),
                created_at=started_at,
            )
            try:
                self.db.add(failed_run)
                self.db.flush()
                self.db.commit()
            except Exception:
                self.db.rollback()

            return {
                "status": "FAILED",
                "idempotent_hit": False,
                "network_run_id": run_id,
                "run_id": run_id,
                "dataset_hash": dataset_hash,
                "error": str(exc),
            }

    # ------------------------------------------------------------
    # Read accessors
    # ------------------------------------------------------------

    def get_run(self, run_id: Optional[str] = None) -> Optional[NetworkFlowRun]:
        """Retrieve the requested tenant-scoped run."""
        if run_id is None:
            return self.run_repo.get_latest_run()
        return self.run_repo.get_by_run_id(run_id)

    def get_run_by_id(self, run_id: str) -> Optional[NetworkFlowRun]:
        return self.run_repo.get_by_id(run_id)

    def get_flow_run(self, run_id: str) -> Optional[NetworkFlowRun]:
        return self.run_repo.get_by_id(run_id)

    def get_network_run(self, run_id: str) -> Optional[NetworkFlowRun]:
        return self.run_repo.get_by_id(run_id)

    def get_intelligence_run(self, run_id: str) -> Optional[NetworkFlowRun]:
        return self.run_repo.get_by_id(run_id)

    def get_latest_run(self) -> Optional[NetworkFlowRun]:
        return self.run_repo.get_latest_run()

    def get_provenance(self, run_id: str) -> Optional[Dict[str, Any]]:
        return self.run_repo.get_provenance(run_id)

    def get_nodes(self, run_id: str) -> List[NetworkNodeSnapshot]:
        return self.node_repo.get_by_run_id(run_id)

    def get_node_snapshots(self, run_id: str) -> List[NetworkNodeSnapshot]:
        return self.get_nodes(run_id)

    def get_network_nodes(self, run_id: str) -> List[NetworkNodeSnapshot]:
        return self.get_nodes(run_id)

    def get_node(self, node_id: str, run_id: Optional[str] = None) -> Optional[NetworkNodeSnapshot]:
        return self.node_repo.get_by_node_id(node_id, run_id)

    def get_node_by_id(self, node_id: str, run_id: Optional[str] = None) -> Optional[NetworkNodeSnapshot]:
        return self.get_node(node_id, run_id)

    def get_edges(self, run_id: str) -> List[NetworkEdgeSnapshot]:
        return self.edge_repo.get_by_run_id(run_id)

    def get_edge_snapshots(self, run_id: str) -> List[NetworkEdgeSnapshot]:
        return self.get_edges(run_id)

    def get_network_edges(self, run_id: str) -> List[NetworkEdgeSnapshot]:
        return self.get_edges(run_id)

    def get_edge(self, edge_id: str, run_id: Optional[str] = None) -> Optional[NetworkEdgeSnapshot]:
        return self.edge_repo.get_by_edge_id(edge_id, run_id)

    def get_edge_by_id(self, edge_id: str, run_id: Optional[str] = None) -> Optional[NetworkEdgeSnapshot]:
        return self.get_edge(edge_id, run_id)

    def get_risks(self, run_id: str) -> List[NetworkRiskSnapshot]:
        return self.risk_repo.get_by_run_id(run_id)

    def get_risk_snapshots(self, run_id: str) -> List[NetworkRiskSnapshot]:
        return self.get_risks(run_id)

    def get_network_risks(self, run_id: str) -> List[NetworkRiskSnapshot]:
        return self.get_risks(run_id)

    def get_risk(self, risk_id: str, run_id: Optional[str] = None) -> Optional[NetworkRiskSnapshot]:
        return self.risk_repo.get_by_risk_id(risk_id, run_id)

    def get_risk_by_id(self, risk_id: str, run_id: Optional[str] = None) -> Optional[NetworkRiskSnapshot]:
        return self.get_risk(risk_id, run_id)

    def get_optimization_run(self, run_id: str) -> Optional[NetworkOptimizationRun]:
        return self.opt_repo.get_by_run_id(run_id)

    def get_optimization(self, run_id: str) -> Optional[NetworkOptimizationRun]:
        return self.get_optimization_run(run_id)

    def get_optimization_results(self, run_id: str) -> Dict[str, Any]:
        opt = self.get_optimization_run(run_id)
        if opt and opt.results_json:
            try:
                parsed = json.loads(str(opt.results_json))
                return cast(Dict[str, Any], parsed) if isinstance(parsed, dict) else {}
            except Exception:
                return {}
        return {}

    def get_metrics(self, run_id: str) -> Dict[str, int]:
        return {
            "node_count": len(self.get_nodes(run_id)),
            "edge_count": len(self.get_edges(run_id)),
            "risk_count": len(self.get_risks(run_id)),
        }

    def get_topology(self, run_id: str) -> Dict[str, Any]:
        nodes = self.get_nodes(run_id)
        edges = self.get_edges(run_id)

        return {
            "nodes": [
                {
                    "node_id": node.node_id,
                    "node_name": node.node_name,
                    "node_type": node.node_type,
                }
                for node in nodes
            ],
            "edges": [
                {
                    "id": edge.id,
                    "edge_id": edge.edge_id,
                    "source_node_id": edge.source_node_id,
                    "destination_node_id": edge.destination_node_id,
                    "sku_id": edge.sku_id,
                }
                for edge in edges
            ],
        }

    def get_summary(self, run_id: str) -> Optional[Dict[str, Any]]:
        return self.get_provenance(run_id)

    run_network_flow = run_network_intelligence


# Backward-compatible alias
NetworkFlowService = NetworkIntelligenceService
