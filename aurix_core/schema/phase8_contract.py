"""Output contract schema for Phase 7A Network Foundation and Multi-Echelon Intelligence."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from aurix_core.schema.phase5_contract import MissingInput, TrackedValue, ValueState


class NodeType(str, Enum):
    SUPPLIER = "SUPPLIER"
    PLANT = "PLANT"
    FACTORY = "FACTORY"
    WAREHOUSE = "WAREHOUSE"
    DISTRIBUTION_CENTER = "DISTRIBUTION_CENTER"
    DC = "DC"
    CROSS_DOCK = "CROSS_DOCK"
    RETAILER = "RETAILER"
    CUSTOMER = "CUSTOMER"
    CUSTOMER_REGION = "CUSTOMER_REGION"
    PORT = "PORT"
    TRANSIT_HUB = "TRANSIT_HUB"
    UNKNOWN = "UNKNOWN"


class NetworkRiskIndicator(str, Enum):
    SINGLE_SOURCE_DEPENDENCY = "SINGLE_SOURCE_DEPENDENCY"
    SINGLE_NODE_DEPENDENCY = "SINGLE_NODE_DEPENDENCY"
    HIGH_FLOW_CONCENTRATION = "HIGH_FLOW_CONCENTRATION"
    CAPACITY_UNKNOWN = "CAPACITY_UNKNOWN"
    CAPACITY_CONSTRAINED = "CAPACITY_CONSTRAINED"
    SERVICE_EXPOSURE = "SERVICE_EXPOSURE"
    LOGISTICS_EXPOSURE = "LOGISTICS_EXPOSURE"
    INVENTORY_IMBALANCE = "INVENTORY_IMBALANCE"
    BULLWHIP_AMPLIFICATION = "BULLWHIP_AMPLIFICATION"
    NOT_ASSESSABLE = "NOT_ASSESSABLE"


class NodeIdentity(BaseModel):
    node_id: str
    node_type: NodeType
    node_name: str
    location: Optional[str] = None
    country: Optional[str] = None
    region: Optional[str] = None
    capacity: TrackedValue
    inventory: TrackedValue
    demand: TrackedValue
    service_level: TrackedValue
    value_state: ValueState


class NetworkEdge(BaseModel):
    source_node_id: str
    destination_node_id: str
    sku_id: str
    flow_quantity: TrackedValue
    flow_frequency: Optional[str] = None
    lead_time_days: TrackedValue
    transport_mode: Optional[str] = None
    supplier_id: Optional[str] = None
    carrier_id: Optional[str] = None
    cost: TrackedValue
    currency: str = "USD"
    service_level: Optional[float] = None


class NodeFlowMetrics(BaseModel):
    node_id: str
    inbound_quantity: TrackedValue
    outbound_quantity: TrackedValue
    net_flow: TrackedValue
    upstream_node_count: int
    downstream_node_count: int


class VulnerabilitySummary(BaseModel):
    single_source_dependencies: List[str] = Field(default_factory=list)
    single_node_dependencies: List[str] = Field(default_factory=list)
    high_flow_bottlenecks: List[str] = Field(default_factory=list)
    supplier_concentration_ratio: Optional[float] = None
    customer_concentration_ratio: Optional[float] = None
    risk_indicators: List[NetworkRiskIndicator] = Field(default_factory=list)


class BullwhipMetrics(BaseModel):
    sku_id: str
    echelon_pair: str
    variance_upstream: float
    variance_downstream: float
    bullwhip_ratio: TrackedValue
    status: str
    reason: Optional[str] = None


class InventoryImbalanceIndicator(BaseModel):
    sku_id: str
    nodes_compared: List[str] = Field(default_factory=list)
    coverage_days_by_node: Dict[str, float] = Field(default_factory=dict)
    imbalance_detected: bool
    description: str


class PortfolioNetworkSummary(BaseModel):
    total_nodes: int
    total_edges: int
    node_type_distribution: Dict[str, int] = Field(default_factory=dict)
    total_skus_mapped: int
    critical_vulnerabilities_count: int
    bullwhip_amplifications_count: int


class Phase8InputContract(BaseModel):
    status: str
    vulnerabilities: VulnerabilitySummary
    portfolio_summary: PortfolioNetworkSummary
    missing_inputs: List[MissingInput] = Field(default_factory=list)
    nodes: Dict[str, NodeIdentity] = Field(default_factory=dict)
    edges: List[NetworkEdge] = Field(default_factory=list)
    node_flow_metrics: Dict[str, NodeFlowMetrics] = Field(default_factory=dict)
    bullwhip_metrics: List[BullwhipMetrics] = Field(default_factory=list)
    inventory_imbalances: List[InventoryImbalanceIndicator] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    provenance: Dict[str, Any] = Field(default_factory=dict)
