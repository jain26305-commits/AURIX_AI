"""Multi-echelon flow mapping, aggregation, and capacity utilization engine for supply network nodes."""

from collections import defaultdict
from typing import Any, Dict, List, Optional, Set
from aurix_core.network.config import NetworkConfiguration
from aurix_core.schema.phase5_contract import TrackedValue, ValueState
from aurix_core.schema.phase8_contract import NetworkEdge, NodeFlowMetrics, NodeIdentity


class NetworkFlowEngine:
    """Calculates inbound, outbound, net material flows, and capacity utilization across multi-echelon supply network nodes."""

    @classmethod
    def calculate_node_flows(
        cls,
        nodes: Dict[str, NodeIdentity],
        edges: List[NetworkEdge],
        filter_sku_id: str = "",
    ) -> Dict[str, NodeFlowMetrics]:
        """
        Computes inbound quantity, outbound quantity, net flow, and node degree counts for every node.
        Can optionally filter flows for a specific SKU ID.
        """
        inbound_qty: Dict[str, float] = defaultdict(float)
        outbound_qty: Dict[str, float] = defaultdict(float)
        has_inbound: Dict[str, bool] = defaultdict(bool)
        has_outbound: Dict[str, bool] = defaultdict(bool)

        upstream_nodes: Dict[str, Set[str]] = defaultdict(set)
        downstream_nodes: Dict[str, Set[str]] = defaultdict(set)

        for edge in edges:
            if filter_sku_id and edge.sku_id != filter_sku_id:
                continue

            src = edge.source_node_id
            dst = edge.destination_node_id

            upstream_nodes[dst].add(src)
            downstream_nodes[src].add(dst)

            qty_obj = edge.flow_quantity
            if qty_obj and qty_obj.value is not None:
                try:
                    qty_val = float(qty_obj.value)
                    outbound_qty[src] += qty_val
                    inbound_qty[dst] += qty_val
                    has_outbound[src] = True
                    has_inbound[dst] = True
                except (ValueError, TypeError):
                    pass

        flow_metrics: Dict[str, NodeFlowMetrics] = {}

        for nid in nodes.keys():
            in_val = inbound_qty[nid] if has_inbound[nid] else None
            out_val = outbound_qty[nid] if has_outbound[nid] else None

            in_tv = TrackedValue(
                value=round(in_val, 2) if in_val is not None else None,
                state=ValueState.DERIVED if in_val is not None else ValueState.UNAVAILABLE,
                source="AGGREGATED_EDGE_INBOUND" if in_val is not None else "UNAVAILABLE",
            )

            out_tv = TrackedValue(
                value=round(out_val, 2) if out_val is not None else None,
                state=ValueState.DERIVED if out_val is not None else ValueState.UNAVAILABLE,
                source="AGGREGATED_EDGE_OUTBOUND" if out_val is not None else "UNAVAILABLE",
            )

            if in_val is not None or out_val is not None:
                net_val = (in_val or 0.0) - (out_val or 0.0)
                net_tv = TrackedValue(
                    value=round(net_val, 2),
                    state=ValueState.DERIVED,
                    source="NET_FLOW_CALCULATION",
                )
            else:
                net_tv = TrackedValue(
                    value=None,
                    state=ValueState.UNAVAILABLE,
                    source="UNAVAILABLE",
                )

            flow_metrics[nid] = NodeFlowMetrics(
                node_id=nid,
                inbound_quantity=in_tv,
                outbound_quantity=out_tv,
                net_flow=net_tv,
                upstream_node_count=len(upstream_nodes[nid]),
                downstream_node_count=len(downstream_nodes[nid]),
            )

        return flow_metrics

    @classmethod
    def calculate_capacity_utilization(
        cls,
        nodes: Dict[str, NodeIdentity],
        flow_metrics: Dict[str, NodeFlowMetrics],
        config: Optional[NetworkConfiguration] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Calculates capacity utilization for nodes where both capacity and flow exist.
        Utilization = Flow / Capacity, classified by thresholds (NORMAL, ELEVATED, BOTTLENECK).
        """
        cfg = config or NetworkConfiguration()
        utilization_results: Dict[str, Dict[str, Any]] = {}

        for nid, node in nodes.items():
            cap_obj = node.capacity
            if not cap_obj or cap_obj.value is None or float(cap_obj.value) <= 0.0:
                utilization_results[nid] = {
                    "utilization": None,
                    "status": "UNKNOWN",
                    "reason": "MISSING_OR_ZERO_CAPACITY",
                }
                continue

            capacity = float(cap_obj.value)
            metrics = flow_metrics.get(nid)
            if not metrics:
                utilization_results[nid] = {
                    "utilization": 0.0,
                    "status": "NORMAL",
                    "reason": "ZERO_FLOW",
                }
                continue

            in_flow = float(metrics.inbound_quantity.value) if (metrics.inbound_quantity and metrics.inbound_quantity.value is not None) else 0.0
            out_flow = float(metrics.outbound_quantity.value) if (metrics.outbound_quantity and metrics.outbound_quantity.value is not None) else 0.0
            active_flow = max(in_flow, out_flow)

            utilization = round(active_flow / capacity, 4)

            status = "NORMAL"
            if utilization >= cfg.capacity_bottleneck_threshold:
                status = "BOTTLENECK"
            elif utilization >= cfg.capacity_elevated_threshold:
                status = "ELEVATED"

            utilization_results[nid] = {
                "utilization": utilization,
                "status": status,
                "reason": f"UTILIZATION_{status}",
            }

        return utilization_results