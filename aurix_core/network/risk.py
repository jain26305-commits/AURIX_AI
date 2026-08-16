"""Network vulnerability, concentration, bottleneck, and inventory imbalance analyzer."""

from collections import defaultdict
from typing import Dict, List, Optional, Set, Tuple

from aurix_core.network.config import NetworkConfiguration
from aurix_core.schema.phase8_contract import (
    InventoryImbalanceIndicator,
    NetworkEdge,
    NetworkRiskIndicator,
    NodeFlowMetrics,
    NodeIdentity,
    NodeType,
    VulnerabilitySummary,
)


class NetworkRiskAnalyzer:
    """Analyzes structural vulnerabilities, concentrations, capacity bottlenecks, and inventory imbalances."""

    @classmethod
    def analyze_vulnerabilities(
        cls,
        nodes: Dict[str, NodeIdentity],
        edges: List[NetworkEdge],
        flow_metrics: Dict[str, NodeFlowMetrics],
        config: Optional[NetworkConfiguration] = None,
    ) -> Tuple[VulnerabilitySummary, List[InventoryImbalanceIndicator]]:
        cfg = config or NetworkConfiguration()

        single_sources: List[str] = []
        single_nodes: List[str] = []
        high_flow_bottlenecks: List[str] = []
        risk_indicators: List[NetworkRiskIndicator] = []

        # 1. Single-Point-of-Failure & Single-Node Dependency Detection
        upstream_suppliers_by_dst: Dict[str, Set[str]] = defaultdict(set)
        upstream_nodes_by_dst: Dict[str, Set[str]] = defaultdict(set)
        supplier_flow_shares: Dict[str, float] = defaultdict(float)
        customer_flow_shares: Dict[str, float] = defaultdict(float)

        for edge in edges:
            src = edge.source_node_id
            dst = edge.destination_node_id

            upstream_nodes_by_dst[dst].add(src)

            if edge.supplier_id:
                upstream_suppliers_by_dst[dst].add(edge.supplier_id)

            qty_val = (
                float(edge.flow_quantity.value)
                if (edge.flow_quantity and edge.flow_quantity.value is not None)
                else 0.0
            )
            if qty_val > 0.0:
                if nodes.get(src) and nodes[src].node_type == NodeType.SUPPLIER:
                    supplier_flow_shares[src] += qty_val

                if nodes.get(dst) and nodes[dst].node_type in (NodeType.CUSTOMER, NodeType.CUSTOMER_REGION):
                    customer_flow_shares[dst] += qty_val

        for dst, suppliers in upstream_suppliers_by_dst.items():
            if len(suppliers) == 1:
                solo_sup = next(iter(suppliers))
                single_sources.append(f"Destination {dst} depends solely on Supplier {solo_sup}")

        for dst, up_nodes in upstream_nodes_by_dst.items():
            if len(up_nodes) == 1:
                solo_node = next(iter(up_nodes))
                single_nodes.append(f"Node {dst} fed solely by Node {solo_node}")

        if single_sources:
            risk_indicators.append(NetworkRiskIndicator.SINGLE_SOURCE_DEPENDENCY)

        if single_nodes:
            risk_indicators.append(NetworkRiskIndicator.SINGLE_NODE_DEPENDENCY)

        # 2. Supplier & Customer Concentration Ratios (relative to echelon total flow)
        sup_ratio: Optional[float] = None
        total_sup_flow = sum(supplier_flow_shares.values())
        if total_sup_flow > 0.0:
            top_sup_flow = max(supplier_flow_shares.values())
            sup_ratio = round(top_sup_flow / total_sup_flow, 4)
            if sup_ratio >= cfg.top_supplier_share_threshold:
                risk_indicators.append(NetworkRiskIndicator.HIGH_FLOW_CONCENTRATION)

        cust_ratio: Optional[float] = None
        total_cust_flow = sum(customer_flow_shares.values())
        if total_cust_flow > 0.0:
            top_cust_flow = max(customer_flow_shares.values())
            cust_ratio = round(top_cust_flow / total_cust_flow, 4)

        # 3. High-Flow & Capacity Bottleneck Detection
        all_outbound_flows = [
            float(m.outbound_quantity.value)
            for m in flow_metrics.values()
            if m.outbound_quantity and m.outbound_quantity.value is not None and float(m.outbound_quantity.value) > 0.0
        ]

        if all_outbound_flows:
            all_outbound_flows.sort()
            p_idx = int(len(all_outbound_flows) * cfg.high_flow_percentile_threshold)
            high_flow_cutoff = all_outbound_flows[min(p_idx, len(all_outbound_flows) - 1)]

            for nid, metric in flow_metrics.items():
                out_val = (
                    float(metric.outbound_quantity.value)
                    if (metric.outbound_quantity and metric.outbound_quantity.value is not None)
                    else 0.0
                )
                if out_val >= high_flow_cutoff and out_val > 0.0:
                    node_obj = nodes.get(nid)
                    cap_obj = node_obj.capacity if node_obj else None

                    if cap_obj and cap_obj.value is not None and float(cap_obj.value) > 0.0:
                        cap_val = float(cap_obj.value)
                        utilization = out_val / cap_val
                        if utilization >= cfg.capacity_utilization_bottleneck_threshold:
                            high_flow_bottlenecks.append(
                                f"Node {nid} (Capacity Constrained: {utilization * 100:.1f}% utilization)"
                            )
                            if NetworkRiskIndicator.CAPACITY_CONSTRAINED not in risk_indicators:
                                risk_indicators.append(NetworkRiskIndicator.CAPACITY_CONSTRAINED)
                        else:
                            high_flow_bottlenecks.append(f"Node {nid} (High Flow Node: {out_val:.1f} units)")
                    else:
                        high_flow_bottlenecks.append(f"Node {nid} (High Flow Node, Capacity Unknown)")
                        if NetworkRiskIndicator.CAPACITY_UNKNOWN not in risk_indicators:
                            risk_indicators.append(NetworkRiskIndicator.CAPACITY_UNKNOWN)

        # 4. Inventory Imbalance Indicators across Echelons
        imbalances: List[InventoryImbalanceIndicator] = []
        node_coverage_by_sku: Dict[str, Dict[str, float]] = defaultdict(dict)

        for edge in edges:
            sku = edge.sku_id
            for nid in (edge.source_node_id, edge.destination_node_id):
                node_item = nodes.get(nid)
                if node_item and node_item.inventory and node_item.inventory.value is not None:
                    inv_units = float(node_item.inventory.value)
                    demand_units = (
                        float(node_item.demand.value)
                        if (
                            node_item.demand
                            and node_item.demand.value is not None
                            and float(node_item.demand.value) > 0.0
                        )
                        else 1.0
                    )
                    cov_days = inv_units / demand_units
                    node_coverage_by_sku[sku][nid] = round(cov_days, 1)

        for sku, cov_map in node_coverage_by_sku.items():
            if len(cov_map) >= 2:
                max_cov = max(cov_map.values())
                min_cov = min(cov_map.values())

                if min_cov > 0.0 and (max_cov / min_cov) >= cfg.imbalance_coverage_ratio_threshold:
                    imbalances.append(
                        InventoryImbalanceIndicator(
                            sku_id=sku,
                            nodes_compared=list(cov_map.keys()),
                            coverage_days_by_node=cov_map,
                            imbalance_detected=True,
                            description=f"Significant coverage ratio disparity detected ({max_cov:.1f}d vs {min_cov:.1f}d).",
                        )
                    )
                    if NetworkRiskIndicator.INVENTORY_IMBALANCE not in risk_indicators:
                        risk_indicators.append(NetworkRiskIndicator.INVENTORY_IMBALANCE)

        if not risk_indicators:
            risk_indicators.append(NetworkRiskIndicator.NOT_ASSESSABLE)

        vulnerability_summary = VulnerabilitySummary(
            single_source_dependencies=single_sources,
            single_node_dependencies=single_nodes,
            high_flow_bottlenecks=high_flow_bottlenecks,
            supplier_concentration_ratio=sup_ratio,
            customer_concentration_ratio=cust_ratio,
            risk_indicators=risk_indicators,
        )

        return vulnerability_summary, imbalances