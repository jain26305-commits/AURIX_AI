"""Autonomous capability discovery and prerequisites evaluation engine for Phase 9."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from aurix_core.intelligence.readiness import FreshnessState, ReadinessAssessment


class CapabilityStatus(str, Enum):
    """Execution eligibility states for AURIX analytical capabilities."""
    AVAILABLE = "AVAILABLE"
    PARTIAL = "PARTIAL"
    UNAVAILABLE = "UNAVAILABLE"
    BLOCKED = "BLOCKED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    WAITING_FOR_INPUT = "WAITING_FOR_INPUT"
    STALE_DATA = "STALE_DATA"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class Domain(str, Enum):
    """Canonical AURIX analytical domains."""
    DEMAND = "DEMAND"
    FORECASTING = "FORECASTING"
    INVENTORY = "INVENTORY"
    SUPPLY = "SUPPLY"
    LOGISTICS = "LOGISTICS"
    NETWORK = "NETWORK"
    DECISION = "DECISION"
    ECONOMICS = "ECONOMICS"


class PrerequisiteRequirement(BaseModel):
    """Defines entity, field, completeness, and historical prerequisites for a capability."""
    primary_entity: str
    required_fields: List[str] = Field(default_factory=list)
    optional_fields: List[str] = Field(default_factory=list)
    min_history_periods: int = 0
    min_record_completeness_pct: float = 95.0
    upstream_capabilities: List[str] = Field(default_factory=list)


class CapabilityDefinition(BaseModel):
    """Metadata and prerequisite rules for a single capability."""
    name: str
    domain: Domain
    description: str
    prerequisites: PrerequisiteRequirement


class DiscoveredCapability(BaseModel):
    """Evaluated status, evidence quality, and diagnostic details of a capability."""
    name: str
    domain: Domain
    status: CapabilityStatus
    freshness: FreshnessState = FreshnessState.UNKNOWN
    quality_score: float = Field(default=0.0, ge=0.0, le=1.0)
    completeness_pct: float = Field(default=0.0, ge=0.0, le=100.0)
    record_completeness_pct: float = Field(default=0.0, ge=0.0, le=100.0)
    missing_prerequisites: List[str] = Field(default_factory=list)
    partially_populated_fields: List[str] = Field(default_factory=list)
    missing_upstream: List[str] = Field(default_factory=list)
    diagnostic_reasons: List[str] = Field(default_factory=list)
    recommended_actions: List[str] = Field(default_factory=list)


class CapabilityDiscoveryReport(BaseModel):
    """Portfolio-wide capability discovery report."""
    capabilities: Dict[str, DiscoveredCapability] = Field(default_factory=dict)
    total_available: int = 0
    total_partial: int = 0
    total_unavailable: int = 0
    overall_status: str = "COMPUTED"
    provenance: Dict[str, Any] = Field(default_factory=dict)


class CapabilityDiscoveryEngine:
    """Evaluates canonical readiness against the formal AURIX Capability Registry."""

    REGISTRY: Dict[str, CapabilityDefinition] = {
        # 1. DEMAND INTELLIGENCE
        "DEMAND_CLASSIFICATION": CapabilityDefinition(
            name="DEMAND_CLASSIFICATION",
            domain=Domain.DEMAND,
            description="Statistical demand categorization (Smooth, Intermittent, Lumpy, Erratic).",
            prerequisites=PrerequisiteRequirement(
                primary_entity="demand_history",
                required_fields=["sku_id", "date", "quantity"],
                min_history_periods=3,
                min_record_completeness_pct=95.0,
            ),
        ),
        # 2. FORECASTING INTELLIGENCE
        "DEMAND_FORECASTING": CapabilityDefinition(
            name="DEMAND_FORECASTING",
            domain=Domain.FORECASTING,
            description="Champion model forecast generation, backtesting, and prediction intervals.",
            prerequisites=PrerequisiteRequirement(
                primary_entity="demand_history",
                required_fields=["sku_id", "date", "quantity"],
                min_history_periods=6,
                min_record_completeness_pct=95.0,
                upstream_capabilities=["DEMAND_CLASSIFICATION"],
            ),
        ),
        # 3. INVENTORY INTELLIGENCE
        "SAFETY_STOCK_ROP": CapabilityDefinition(
            name="SAFETY_STOCK_ROP",
            domain=Domain.INVENTORY,
            description="Dynamic safety stock, reorder point, and replenishment calculations.",
            prerequisites=PrerequisiteRequirement(
                primary_entity="inventory_levels",
                required_fields=["sku_id", "node_id", "on_hand_units", "lead_time_days"],
                optional_fields=["service_level", "holding_cost_rate"],
                min_record_completeness_pct=90.0,
                upstream_capabilities=["DEMAND_FORECASTING"],
            ),
        ),
        "INVENTORY_POSITION_RISK": CapabilityDefinition(
            name="INVENTORY_POSITION_RISK",
            domain=Domain.INVENTORY,
            description="Stockout imminent risk, coverage duration, and excess inventory detection.",
            prerequisites=PrerequisiteRequirement(
                primary_entity="inventory_levels",
                required_fields=["sku_id", "node_id", "on_hand_units"],
                min_record_completeness_pct=90.0,
                upstream_capabilities=["DEMAND_FORECASTING"],
            ),
        ),
        # 4. SUPPLY INTELLIGENCE
        "SUPPLIER_PERFORMANCE_RISK": CapabilityDefinition(
            name="SUPPLIER_PERFORMANCE_RISK",
            domain=Domain.SUPPLY,
            description="Supplier on-time delivery, lead-time variance, and risk tier evaluation.",
            prerequisites=PrerequisiteRequirement(
                primary_entity="purchase_orders",
                required_fields=["po_id", "supplier_id", "promised_date", "actual_delivery_date"],
                min_history_periods=3,
                min_record_completeness_pct=90.0,
            ),
        ),
        "SUPPLIER_SELECTION": CapabilityDefinition(
            name="SUPPLIER_SELECTION",
            domain=Domain.SUPPLY,
            description="Multi-criteria supplier ranking, MOQ evaluation, and allocation recommendations.",
            prerequisites=PrerequisiteRequirement(
                primary_entity="supplier_catalog",
                required_fields=["supplier_id", "sku_id", "unit_price", "moq"],
                min_record_completeness_pct=90.0,
                upstream_capabilities=["SUPPLIER_PERFORMANCE_RISK"],
            ),
        ),
        # 5. LOGISTICS INTELLIGENCE
        "SHIPMENT_TRACKING_ETA": CapabilityDefinition(
            name="SHIPMENT_TRACKING_ETA",
            domain=Domain.LOGISTICS,
            description="In-transit tracking, dynamic ETA estimation, and carrier SLA evaluation.",
            prerequisites=PrerequisiteRequirement(
                primary_entity="shipments",
                required_fields=["shipment_id", "carrier_id", "origin_node", "destination_node", "status"],
                optional_fields=["planned_eta", "current_location"],
                min_record_completeness_pct=85.0,
            ),
        ),
        # 6. NETWORK INTELLIGENCE
        "NETWORK_TOPOLOGY_BOTTLENECK": CapabilityDefinition(
            name="NETWORK_TOPOLOGY_BOTTLENECK",
            domain=Domain.NETWORK,
            description="Multi-echelon network topology mapping, bottleneck, and single-source risk analysis.",
            prerequisites=PrerequisiteRequirement(
                primary_entity="network_nodes",
                required_fields=["node_id", "node_type", "capacity"],
                optional_fields=["inflow_rate", "outflow_rate"],
                min_record_completeness_pct=90.0,
            ),
        ),
        # 7. DECISION INTELLIGENCE
        "INVENTORY_REBALANCING": CapabilityDefinition(
            name="INVENTORY_REBALANCING",
            domain=Domain.DECISION,
            description="Multi-facility lateral stock rebalancing and transfer feasibility optimization.",
            prerequisites=PrerequisiteRequirement(
                primary_entity="rebalancing_candidates",
                required_fields=["sku_id", "source_node", "destination_node"],
                min_record_completeness_pct=90.0,
                upstream_capabilities=["SAFETY_STOCK_ROP", "NETWORK_TOPOLOGY_BOTTLENECK"],
            ),
        ),
        # 8. FINANCIAL INTELLIGENCE & SCENARIOS
        "WORKING_CAPITAL_TCO": CapabilityDefinition(
            name="WORKING_CAPITAL_TCO",
            domain=Domain.ECONOMICS,
            description="Total cost of ownership, working capital exposure, and holding cost evaluation.",
            prerequisites=PrerequisiteRequirement(
                primary_entity="item_costs",
                required_fields=["sku_id", "unit_cost", "currency"],
                min_record_completeness_pct=90.0,
                upstream_capabilities=["SAFETY_STOCK_ROP"],
            ),
        ),
        "SCENARIO_SIMULATION": CapabilityDefinition(
            name="SCENARIO_SIMULATION",
            domain=Domain.ECONOMICS,
            description="What-if scenario simulations (demand shocks, tariff changes, freight disruptions).",
            prerequisites=PrerequisiteRequirement(
                primary_entity="scenario_parameters",
                required_fields=["scenario_type", "multiplier"],
                min_record_completeness_pct=90.0,
                upstream_capabilities=["WORKING_CAPITAL_TCO"],
            ),
        ),
    }

    @classmethod
    def discover(
        cls,
        readiness_map: Dict[str, ReadinessAssessment],
        history_depth_map: Optional[Dict[str, int]] = None,
        active_upstream_capabilities: Optional[List[str]] = None,
    ) -> CapabilityDiscoveryReport:
        """Evaluates portfolio readiness against registry prerequisites to discover active/blocked capabilities."""
        history_depths = history_depth_map or {}
        available_upstream = set(active_upstream_capabilities or [])
        discovered: Dict[str, DiscoveredCapability] = {}

        total_avail = 0
        total_part = 0
        total_unavail = 0

        for cap_name, cap_def in cls.REGISTRY.items():
            reqs = cap_def.prerequisites
            entity_name = reqs.primary_entity
            readiness = readiness_map.get(entity_name)

            missing_pre: List[str] = []
            partially_pop: List[str] = []
            missing_up: List[str] = []
            diagnostics: List[str] = []
            actions: List[str] = []

            # 1. Check Upstream Dependencies
            for up_cap in reqs.upstream_capabilities:
                if up_cap not in available_upstream:
                    missing_up.append(up_cap)
                    diagnostics.append(f"BLOCKED_BY_UPSTREAM_CAPABILITY: {up_cap}")

            # 2. Check Entity and Field Readiness
            if readiness is None:
                missing_pre.extend(reqs.required_fields)
                diagnostics.append(f"MISSING_PRIMARY_ENTITY: {entity_name}")
                actions.append(f"Provide canonical data table for {entity_name}")
            else:
                if readiness.missing_fields:
                    missing_pre.extend(readiness.missing_fields)
                    diagnostics.append(f"MISSING_REQUIRED_FIELDS: {', '.join(readiness.missing_fields)}")
                    actions.append(
                        f"Upload or connect {entity_name} with fields: {', '.join(readiness.missing_fields)}"
                    )

                if readiness.partially_populated_fields:
                    partially_pop.extend(readiness.partially_populated_fields)
                    diagnostics.append(
                        f"PARTIALLY_POPULATED_FIELDS: {', '.join(readiness.partially_populated_fields)}"
                    )

                if readiness.record_completeness_pct < reqs.min_record_completeness_pct:
                    diagnostics.append(
                        f"LOW_RECORD_COMPLETENESS: {readiness.record_completeness_pct}% "
                        f"(required >= {reqs.min_record_completeness_pct}%)"
                    )

            # 3. Check Statistical History Depth
            observed_depth = history_depths.get(entity_name, 0)
            if reqs.min_history_periods > 0 and observed_depth < reqs.min_history_periods:
                diagnostics.append(
                    f"INSUFFICIENT_HISTORY: Found {observed_depth} periods, required {reqs.min_history_periods}"
                )
                actions.append(f"Provide at least {reqs.min_history_periods} historical periods for {entity_name}")

            # 4. Check Stale Data
            is_stale = readiness is not None and readiness.freshness in (
                FreshnessState.STALE,
                FreshnessState.VERY_STALE,
            )
            if is_stale and readiness is not None:
                diagnostics.append(f"DATA_FRESHNESS_WARNING: {entity_name} is {readiness.freshness.value}")
                actions.append(f"Refresh canonical {entity_name} records to restore live confidence.")

            # 5. Determine Capability Status
            if missing_up:
                status = CapabilityStatus.BLOCKED
                total_unavail += 1
            elif readiness is None:
                status = CapabilityStatus.UNAVAILABLE
                total_unavail += 1
            elif reqs.min_history_periods > 0 and observed_depth < reqs.min_history_periods:
                status = CapabilityStatus.INSUFFICIENT_EVIDENCE
                total_unavail += 1
            elif missing_pre:
                if readiness.record_completeness_pct > 0.0:
                    status = CapabilityStatus.PARTIAL
                    total_part += 1
                else:
                    status = CapabilityStatus.WAITING_FOR_INPUT
                    total_unavail += 1
            elif readiness.record_completeness_pct < reqs.min_record_completeness_pct:
                status = CapabilityStatus.PARTIAL
                total_part += 1
            elif is_stale:
                status = CapabilityStatus.STALE_DATA
                total_avail += 1
                available_upstream.add(cap_name)
            else:
                status = CapabilityStatus.AVAILABLE
                total_avail += 1
                available_upstream.add(cap_name)

            freshness = readiness.freshness if readiness else FreshnessState.UNKNOWN
            quality = readiness.quality_score if readiness else 0.0
            completeness = readiness.completeness_pct if readiness else 0.0
            rec_completeness = readiness.record_completeness_pct if readiness else 0.0

            discovered[cap_name] = DiscoveredCapability(
                name=cap_name,
                domain=cap_def.domain,
                status=status,
                freshness=freshness,
                quality_score=quality,
                completeness_pct=completeness,
                record_completeness_pct=rec_completeness,
                missing_prerequisites=missing_pre,
                partially_populated_fields=partially_pop,
                missing_upstream=missing_up,
                diagnostic_reasons=diagnostics,
                recommended_actions=actions,
            )

        overall = "COMPLETED" if total_unavail == 0 else "PARTIAL_SUCCESS" if total_avail > 0 else "WAITING_FOR_INPUT"

        return CapabilityDiscoveryReport(
            capabilities=discovered,
            total_available=total_avail,
            total_partial=total_part,
            total_unavailable=total_unavail,
            overall_status=overall,
        )