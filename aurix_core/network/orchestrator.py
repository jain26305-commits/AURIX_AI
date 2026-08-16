"""Master Orchestrator for Phase 7A Network Foundation and Multi-Echelon Intelligence."""

from __future__ import annotations

import datetime
import uuid
from collections.abc import Mapping
from typing import Any, Dict, List, Optional

from aurix_core.network.bullwhip import BullwhipAnalyzer
from aurix_core.network.config import NetworkConfiguration
from aurix_core.network.flow import NetworkFlowEngine
from aurix_core.network.risk import NetworkRiskAnalyzer
from aurix_core.network.topology import NetworkTopologyBuilder
from aurix_core.schema.phase5_contract import MissingInput
from aurix_core.schema.phase8_contract import (
    BullwhipMetrics,
    NetworkEdge,
    NodeIdentity,
    Phase8InputContract,
    PortfolioNetworkSummary,
)

__all__ = ["Phase7AOrchestrator"]


class Phase7AOrchestrator:
    """Master Orchestrator for Phase 7A Network Foundation and Multi-Echelon Intelligence."""

    def __init__(
        self,
        network_data: Optional[Dict[str, Any]] = None,
        upstream_phase_data: Optional[Dict[str, Any]] = None,
        config_override: Optional[Any] = None,
    ) -> None:
        self.network_data = network_data or {}
        self.upstream_data = upstream_phase_data or {}

        if isinstance(config_override, NetworkConfiguration):
            self.config = config_override
        elif isinstance(config_override, dict):
            self.config = NetworkConfiguration(config_override)
        else:
            self.config = NetworkConfiguration()

        self.run_id = str(uuid.uuid4())
        self.timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

    @staticmethod
    def _coerce_records(
        raw_value: Any,
        *,
        id_keys: tuple[str, ...] = (),
    ) -> List[Dict[str, Any]]:
        """
        Normalize supported collection shapes without inventing business records.

        Supported input:
        - list/tuple of mappings
        - mapping of record-id -> mapping
        - single mapping representing one record
        """
        if isinstance(raw_value, Mapping):
            # A single record is recognized by the presence of any configured ID
            # field or common record fields. Otherwise treat the mapping as a
            # record collection keyed by external IDs.
            if any(key in raw_value for key in id_keys):
                return [dict(raw_value)]

            collection: List[Dict[str, Any]] = []
            for external_id, value in raw_value.items():
                if not isinstance(value, Mapping):
                    continue

                record = dict(value)
                if not any(
                    key in record and record[key] not in (None, "")
                    for key in id_keys
                ):
                    if id_keys:
                        record[id_keys[0]] = external_id
                collection.append(record)
            return collection

        if isinstance(raw_value, (list, tuple)):
            return [
                dict(item)
                for item in raw_value
                if isinstance(item, Mapping)
            ]

        return []

    def process_network(self) -> Phase8InputContract:
        missing_inputs: List[MissingInput] = []
        limitations: List[str] = []

        raw_nodes = self._coerce_records(
            self.network_data.get("nodes", []),
            id_keys=("node_id", "id"),
        )
        raw_edges = self._coerce_records(
            self.network_data.get("edges", []),
            id_keys=("edge_id", "id"),
        )
        raw_bullwhip_series = self._coerce_records(
            self.network_data.get("bullwhip_series", []),
            id_keys=("sku_id",),
        )

        # 1. Extract & Build Canonical Node Identities
        nodes: Dict[str, NodeIdentity] = {}

        for index, node_dict in enumerate(raw_nodes):
            nid = str(
                node_dict.get("node_id")
                or node_dict.get("id")
                or ""
            ).strip()

            if not nid:
                limitations.append(
                    f"Skipped node record at position {index}: missing node_id."
                )
                continue

            try:
                raw_type = node_dict.get("node_type")
                parsed_type = NetworkTopologyBuilder.parse_node_type(raw_type)

                node_identity = NetworkTopologyBuilder.build_node_identity(
                    node_id=nid,
                    node_type=parsed_type,
                    name=node_dict.get("node_name"),
                    location=node_dict.get("location"),
                    country=node_dict.get("country"),
                    region=node_dict.get("region"),
                    capacity_units=node_dict.get("capacity_units"),
                    inventory_units=node_dict.get("inventory_units"),
                    demand_units=node_dict.get("demand_units"),
                    service_level=node_dict.get("service_level"),
                )
                nodes[nid] = node_identity
            except (TypeError, ValueError) as exc:
                limitations.append(
                    f"Skipped node '{nid}': {exc}"
                )

        if not nodes:
            missing_inputs.append(
                MissingInput(
                    field="nodes",
                    state="USER_INPUT_REQUIRED",
                    domain="network",
                    severity="CRITICAL",
                    prompt="No valid network node identities were provided.",
                )
            )

        # 2. Build Directed Material/Information Edges
        edges: List[NetworkEdge] = []

        for index, edge_dict in enumerate(raw_edges):
            src = str(
                edge_dict.get("source_node_id")
                or edge_dict.get("source")
                or edge_dict.get("from_node")
                or ""
            ).strip()

            dst = str(
                edge_dict.get("destination_node_id")
                or edge_dict.get("destination")
                or edge_dict.get("to_node")
                or ""
            ).strip()

            sku = str(
                edge_dict.get("sku_id")
                or edge_dict.get("sku")
                or ""
            ).strip()

            if not src or not dst or not sku:
                limitations.append(
                    f"Skipped edge record at position {index}: "
                    "source_node_id, destination_node_id, and sku_id are required."
                )
                continue

            try:
                edge_obj = NetworkTopologyBuilder.build_network_edge(
                    source_id=src,
                    destination_id=dst,
                    sku_id=sku,
                    flow_quantity=edge_dict.get("flow_quantity"),
                    lead_time_days=edge_dict.get("lead_time_days"),
                    transport_mode=edge_dict.get("transport_mode"),
                    supplier_id=edge_dict.get("supplier_id"),
                    carrier_id=edge_dict.get("carrier_id"),
                    cost=edge_dict.get("cost"),
                    # NetworkEdge requires a currency string. USD is the
                    # contract-level default already used by the topology
                    # builder; it is not a fabricated financial calculation.
                    currency=str(edge_dict.get("currency") or "USD"),
                )
                edges.append(edge_obj)
            except (TypeError, ValueError) as exc:
                limitations.append(
                    f"Skipped edge '{src}->{dst}:{sku}': {exc}"
                )

        # Topology Validation & Connectivity Check
        orphan_nodes, missing_sources, missing_dests = (
            NetworkTopologyBuilder.validate_connectivity(
                nodes,
                edges,
            )
        )

        if orphan_nodes:
            limitations.append(
                f"Orphan nodes detected without flow connectivity: {orphan_nodes}"
            )

        if missing_sources:
            limitations.append(
                f"Edges reference unmapped source node IDs: {missing_sources}"
            )

        if missing_dests:
            limitations.append(
                f"Edges reference unmapped destination node IDs: {missing_dests}"
            )

        cycles = NetworkTopologyBuilder.detect_cycles(edges)
        if cycles:
            limitations.append(
                f"Structural network loops/cycles detected: {cycles}"
            )

        # 3. Flow Mapping & Node-Level Net Flows
        node_flow_metrics = NetworkFlowEngine.calculate_node_flows(
            nodes,
            edges,
        )

        # 4. Vulnerabilities, Concentrations, Bottlenecks, and Inventory Imbalances
        vulnerabilities, imbalances = (
            NetworkRiskAnalyzer.analyze_vulnerabilities(
                nodes=nodes,
                edges=edges,
                flow_metrics=node_flow_metrics,
                config=self.config,
            )
        )

        # 5. Bullwhip Effect Variance Amplification Analysis
        bullwhip_results: List[BullwhipMetrics] = []

        for index, bullwhip_dict in enumerate(raw_bullwhip_series):
            b_sku = str(
                bullwhip_dict.get("sku_id")
                or bullwhip_dict.get("sku")
                or ""
            ).strip()

            if not b_sku:
                limitations.append(
                    f"Skipped Bullwhip record at position {index}: missing sku_id."
                )
                continue

            echelon_pair = str(
                bullwhip_dict.get(
                    "echelon_pair",
                    "UPSTREAM_VS_DOWNSTREAM",
                )
            )

            up_orders = bullwhip_dict.get("upstream_orders", [])
            down_demand = bullwhip_dict.get("downstream_demand", [])

            try:
                b_metric = BullwhipAnalyzer.calculate_bullwhip_effect(
                    sku_id=b_sku,
                    echelon_pair=echelon_pair,
                    upstream_orders=up_orders,
                    downstream_demand=down_demand,
                    config=self.config,
                )
                bullwhip_results.append(b_metric)
            except (TypeError, ValueError) as exc:
                limitations.append(
                    f"Skipped Bullwhip calculation for '{b_sku}': {exc}"
                )

        # 6. Portfolio Network Summary
        node_types_dist: Dict[str, int] = {}

        for node in nodes.values():
            t_str = node.node_type.value
            node_types_dist[t_str] = node_types_dist.get(t_str, 0) + 1

        mapped_skus = len({edge.sku_id for edge in edges})
        crit_vuln_count = len(
            vulnerabilities.single_source_dependencies
        ) + len(
            vulnerabilities.single_node_dependencies
        )

        bullwhip_count = len(
            [
                metric
                for metric in bullwhip_results
                if metric.status == "BULLWHIP_AMPLIFIED"
            ]
        )

        summary = PortfolioNetworkSummary(
            total_nodes=len(nodes),
            total_edges=len(edges),
            node_type_distribution=node_types_dist,
            total_skus_mapped=mapped_skus,
            critical_vulnerabilities_count=crit_vuln_count,
            bullwhip_amplifications_count=bullwhip_count,
        )

        status = "COMPUTABLE" if nodes and edges else "USER_INPUT_REQUIRED"

        return Phase8InputContract(
            status=status,
            missing_inputs=missing_inputs,
            nodes=nodes,
            edges=edges,
            node_flow_metrics=node_flow_metrics,
            vulnerabilities=vulnerabilities,
            bullwhip_metrics=bullwhip_results,
            inventory_imbalances=imbalances,
            portfolio_summary=summary,
            limitations=limitations,
            provenance={
                "phase7a_run_id": self.run_id,
                "timestamp": self.timestamp,
                "engine_version": "7.0.0-network-foundation",
            },
        )

    def execute(self) -> Dict[str, Any]:
        """Execute Phase 7A and return its canonical contract as a dictionary."""
        return self.process_network().model_dump()