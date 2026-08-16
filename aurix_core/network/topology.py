"""Network topology builder for node extraction, edge mapping, cycle detection, and connectivity validation."""

from collections import defaultdict
from typing import Dict, List, Optional, Set, Tuple
from aurix_core.schema.phase5_contract import TrackedValue, ValueState
from aurix_core.schema.phase8_contract import NetworkEdge, NodeIdentity, NodeType


class NetworkTopologyBuilder:
    """Builds and validates multi-echelon network nodes, directed edges, and graph connectivity structures."""

    ALIAS_MAP: Dict[str, NodeType] = {
        "SUPPLIER": NodeType.SUPPLIER,
        "VENDOR": NodeType.SUPPLIER,
        "PLANT": NodeType.PLANT,
        "FACTORY": NodeType.PLANT,
        "MANUFACTURING": NodeType.PLANT,
        "WAREHOUSE": NodeType.WAREHOUSE,
        "DEPOT": NodeType.WAREHOUSE,
        "DC": NodeType.DISTRIBUTION_CENTER,
        "DISTRIBUTION_CENTER": NodeType.DISTRIBUTION_CENTER,
        "CUSTOMER": NodeType.CUSTOMER,
        "CLIENT": NodeType.CUSTOMER,
        "CUSTOMER_REGION": NodeType.CUSTOMER,
        "PORT": NodeType.PORT,
        "TRANSIT_HUB": NodeType.TRANSIT_HUB,
        "CROSS_DOCK": NodeType.CROSS_DOCK,
    }

    @classmethod
    def parse_node_type(cls, raw_type: Optional[str]) -> NodeType:
        if not raw_type:
            return NodeType.UNKNOWN
        clean_type = raw_type.strip().upper()
        if clean_type in cls.ALIAS_MAP:
            return cls.ALIAS_MAP[clean_type]
        try:
            return NodeType[clean_type]
        except KeyError:
            return NodeType.UNKNOWN

    @classmethod
    def build_node_identity(
        cls,
        node_id: str,
        node_type: NodeType,
        name: Optional[str] = None,
        location: Optional[str] = None,
        country: Optional[str] = None,
        region: Optional[str] = None,
        capacity_units: Optional[float] = None,
        inventory_units: Optional[float] = None,
        demand_units: Optional[float] = None,
        service_level: Optional[float] = None,
    ) -> NodeIdentity:
        clean_id = str(node_id).strip()
        clean_name = str(name).strip() if name else clean_id

        capacity_valid = capacity_units is not None and capacity_units >= 0.0
        cap_val = float(capacity_units) if (capacity_units is not None and capacity_valid) else None
        capacity_tv = TrackedValue(
            value=cap_val,
            state=ValueState.OBSERVED if capacity_valid else ValueState.UNAVAILABLE,
            source="NODE_RECORD" if capacity_valid else "UNAVAILABLE",
        )

        inv_valid = inventory_units is not None and inventory_units >= 0.0
        inv_val = float(inventory_units) if (inventory_units is not None and inv_valid) else None
        inventory_tv = TrackedValue(
            value=inv_val,
            state=ValueState.DERIVED if inv_valid else ValueState.UNAVAILABLE,
            source="PHASE4_INVENTORY" if inv_valid else "UNAVAILABLE",
        )

        demand_valid = demand_units is not None and demand_units >= 0.0
        dem_val = float(demand_units) if (demand_units is not None and demand_valid) else None
        demand_tv = TrackedValue(
            value=dem_val,
            state=ValueState.DERIVED if demand_valid else ValueState.UNAVAILABLE,
            source="PHASE2_PHASE3_DEMAND" if demand_valid else "UNAVAILABLE",
        )

        service_valid = service_level is not None and 0.0 <= service_level <= 1.0
        serv_val = float(service_level) if (service_level is not None and service_valid) else None
        service_tv = TrackedValue(
            value=serv_val,
            state=ValueState.OBSERVED if service_valid else ValueState.UNAVAILABLE,
            source="HISTORICAL_PERFORMANCE" if service_valid else "UNAVAILABLE",
        )

        has_observed = any([capacity_units is not None, location is not None, name is not None])
        val_state = ValueState.OBSERVED if has_observed else ValueState.INFERRED

        return NodeIdentity(
            node_id=clean_id,
            node_type=node_type,
            node_name=clean_name,
            location=location,
            country=country,
            region=region,
            capacity=capacity_tv,
            inventory=inventory_tv,
            demand=demand_tv,
            service_level=service_tv,
            value_state=val_state,
        )

    @classmethod
    def build_network_edge(
        cls,
        source_id: str,
        destination_id: str,
        sku_id: str,
        flow_quantity: Optional[float],
        lead_time_days: Optional[float] = None,
        transport_mode: Optional[str] = None,
        supplier_id: Optional[str] = None,
        carrier_id: Optional[str] = None,
        cost: Optional[float] = None,
        currency: str = "USD",
    ) -> NetworkEdge:
        clean_src = str(source_id).strip()
        clean_dst = str(destination_id).strip()
        clean_sku = str(sku_id).strip()

        flow_valid = flow_quantity is not None and flow_quantity >= 0.0
        flow_val = float(flow_quantity) if (flow_quantity is not None and flow_valid) else None
        flow_tv = TrackedValue(
            value=flow_val,
            state=ValueState.OBSERVED if flow_valid else ValueState.UNAVAILABLE,
            source="FLOW_RECORD" if flow_valid else "UNAVAILABLE",
        )

        lt_valid = lead_time_days is not None and lead_time_days >= 0.0
        lt_val = float(lead_time_days) if (lead_time_days is not None and lt_valid) else None
        lt_tv = TrackedValue(
            value=lt_val,
            state=ValueState.OBSERVED if lt_valid else ValueState.UNAVAILABLE,
            source="TRANSIT_RECORD" if lt_valid else "UNAVAILABLE",
        )

        cost_valid = cost is not None and cost >= 0.0
        cost_val = float(cost) if (cost is not None and cost_valid) else None
        cost_tv = TrackedValue(
            value=cost_val,
            state=ValueState.OBSERVED if cost_valid else ValueState.UNAVAILABLE,
            source="FREIGHT_RECORD" if cost_valid else "UNAVAILABLE",
        )

        return NetworkEdge(
            source_node_id=clean_src,
            destination_node_id=clean_dst,
            sku_id=clean_sku,
            flow_quantity=flow_tv,
            lead_time_days=lt_tv,
            transport_mode=transport_mode,
            supplier_id=supplier_id,
            carrier_id=carrier_id,
            cost=cost_tv,
            currency=currency,
        )

    @classmethod
    def detect_cycles(cls, edges: List[NetworkEdge]) -> List[List[str]]:
        """Detects directed cycles in the network topology graph using Depth-First Search."""
        adj: Dict[str, List[str]] = defaultdict(list)
        for e in edges:
            adj[e.source_node_id].append(e.destination_node_id)

        visited: Dict[str, int] = defaultdict(int)  # 0: unvisited, 1: visiting, 2: visited
        cycles: List[List[str]] = []
        path: List[str] = []

        def dfs(node: str) -> None:
            visited[node] = 1
            path.append(node)

            for neighbor in adj[node]:
                if visited[neighbor] == 1:
                    cycle_start = path.index(neighbor)
                    cycles.append(path[cycle_start:] + [neighbor])
                elif visited[neighbor] == 0:
                    dfs(neighbor)

            path.pop()
            visited[node] = 2

        nodes_set = set(adj.keys()) | {e.destination_node_id for e in edges}
        for node in nodes_set:
            if visited[node] == 0:
                dfs(node)

        return cycles

    @classmethod
    def validate_connectivity(
        cls,
        nodes: Dict[str, NodeIdentity],
        edges: List[NetworkEdge],
    ) -> Tuple[List[str], List[str], List[str]]:
        """Validates graph connectivity and identifies orphan nodes and missing node references."""
        connected_nodes: Set[str] = set()
        missing_sources: Set[str] = set()
        missing_destinations: Set[str] = set()

        for edge in edges:
            if edge.source_node_id in nodes:
                connected_nodes.add(edge.source_node_id)
            else:
                missing_sources.add(edge.source_node_id)

            if edge.destination_node_id in nodes:
                connected_nodes.add(edge.destination_node_id)
            else:
                missing_destinations.add(edge.destination_node_id)

        orphan_nodes = [nid for nid in nodes.keys() if nid not in connected_nodes]

        return orphan_nodes, list(missing_sources), list(missing_destinations)