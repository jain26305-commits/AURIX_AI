"""Go/No-Go readiness validation gates to prevent optimization on missing or unobserved data."""

from typing import Optional, Tuple
from aurix_core.schema.phase5_contract import ValueState
from aurix_core.schema.phase8_contract import NetworkEdge, NodeIdentity
from aurix_core.schema.phase9_contract import OptimizationStatus


class OptimizationGate:
    """Readiness gates enforcing strict zero-fabrication prerequisites before optimization."""

    @classmethod
    def check_rebalancing_readiness(
        cls,
        source_node: Optional[NodeIdentity],
        dest_node: Optional[NodeIdentity],
        edge: Optional[NetworkEdge] = None,
    ) -> Tuple[bool, OptimizationStatus, str]:
        """Validates if a node-to-node inventory transfer optimization is operationally assessable."""
        if not source_node or not dest_node:
            return False, OptimizationStatus.INSUFFICIENT_DATA, "Source or destination node is missing."

        if source_node.node_id == dest_node.node_id:
            return False, OptimizationStatus.NOT_OPTIMIZABLE, "Source and destination nodes are identical."

        if (
            not source_node.inventory
            or source_node.inventory.state == ValueState.UNAVAILABLE
            or source_node.inventory.value is None
        ):
            return (
                False,
                OptimizationStatus.INSUFFICIENT_DATA,
                f"Source node {source_node.node_id} lacks explicit inventory data.",
            )

        if (
            not dest_node.inventory
            or dest_node.inventory.state == ValueState.UNAVAILABLE
            or dest_node.inventory.value is None
        ):
            return (
                False,
                OptimizationStatus.INSUFFICIENT_DATA,
                f"Destination node {dest_node.node_id} lacks explicit inventory data.",
            )

        if edge is None:
            return (
                False,
                OptimizationStatus.NOT_OPTIMIZABLE,
                f"No validated network edge exists between {source_node.node_id} and {dest_node.node_id}.",
            )

        src_inv_val = float(source_node.inventory.value)
        if src_inv_val <= 0.0:
            return (
                False,
                OptimizationStatus.NOT_OPTIMIZABLE,
                f"Source node {source_node.node_id} has zero or negative inventory.",
            )

        return True, OptimizationStatus.FEASIBLE, "Nodes and network edge are operationally ready for optimization."
