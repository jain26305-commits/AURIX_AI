"""SQLAlchemy ORM models for Phase 7A Multi-Echelon Network Flow and Topology."""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text

from aurix_core.database.engine import Base


class NetworkFlowRun(Base):
    """Execution run record for the Phase 7A Network Flow pipeline."""

    __tablename__ = "network_flow_runs"

    id = Column(String(64), primary_key=True)
    run_id = Column(String(64), nullable=True)
    tenant_id = Column(String(64), nullable=False, index=True)
    dataset_hash = Column(String(64), nullable=False, index=True)
    status = Column(String(32), nullable=False, default="PENDING")
    node_count = Column(Integer, nullable=False, default=0)
    edge_count = Column(Integer, nullable=False, default=0)
    risk_count = Column(Integer, nullable=False, default=0)
    duration_ms = Column(Float, nullable=False, default=0.0)
    configuration = Column(Text, nullable=True)
    provenance = Column(Text, nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


# Backward-compatible domain alias.
NetworkIntelligenceRun = NetworkFlowRun


class NetworkNodeSnapshot(Base):
    """Persistent snapshot of a supply-chain network node."""

    __tablename__ = "network_node_snapshots"

    id = Column(String(64), primary_key=True)
    tenant_id = Column(String(64), nullable=False, index=True)

    run_id = Column(
        String(64),
        ForeignKey("network_flow_runs.id"),
        nullable=False,
        index=True,
    )

    node_id = Column(String(64), nullable=False, index=True)

    # Identity fields are required because they define the entity itself.
    node_name = Column(String(128), nullable=False)
    node_type = Column(String(32), nullable=False)

    # These are legitimately unavailable for some customer datasets.
    location_name = Column(String(128), nullable=True)
    tier_level = Column(Integer, nullable=True)
    holding_cost_rate = Column(Float, nullable=True)
    capacity = Column(Float, nullable=True)

    status = Column(String(32), nullable=False, default="ACTIVE")
    attributes_json = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class NetworkEdgeSnapshot(Base):
    """Persistent snapshot of a directed multi-echelon transport edge."""

    __tablename__ = "network_edge_snapshots"

    id = Column(String(64), primary_key=True)
    tenant_id = Column(String(64), nullable=False, index=True)

    run_id = Column(
        String(64),
        ForeignKey("network_flow_runs.id"),
        nullable=False,
        index=True,
    )

    # Edge identity is required.
    edge_id = Column(String(64), nullable=False, index=True)
    sku_id = Column(String(64), nullable=False)
    source_node_id = Column(String(64), nullable=False, index=True)
    destination_node_id = Column(String(64), nullable=False, index=True)

    # Operational attributes may legitimately be unavailable.
    transport_mode = Column(String(32), nullable=True)
    nominal_lead_time_days = Column(Float, nullable=True)
    unit_transport_cost = Column(Float, nullable=True)
    capacity = Column(Float, nullable=True)

    status = Column(String(32), nullable=False, default="ACTIVE")
    attributes_json = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class NetworkRiskSnapshot(Base):
    """Persistent snapshot of an identified network vulnerability or disruption risk."""

    __tablename__ = "network_risk_snapshots"

    id = Column(String(64), primary_key=True)

    risk_id = Column(String(64), nullable=True, index=True)
    tenant_id = Column(String(64), nullable=False, index=True)

    run_id = Column(
        String(64),
        ForeignKey("network_flow_runs.id"),
        nullable=False,
        index=True,
    )

    node_id = Column(String(64), nullable=True, index=True)

    disruption_probability = Column(Float, nullable=True)
    bottleneck_severity = Column(String(32), nullable=True)
    estimated_days_to_recover = Column(Float, nullable=True)
    risk_score = Column(Float, nullable=True)

    mitigation_strategy = Column(Text, nullable=True)
    evidence_json = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


# Backward-compatible domain alias.
NetworkRiskEvent = NetworkRiskSnapshot


class NetworkOptimizationRun(Base):
    """Persistent record of network-flow topology optimization."""

    __tablename__ = "network_optimization_runs"

    id = Column(String(64), primary_key=True)
    tenant_id = Column(String(64), nullable=False, index=True)

    run_id = Column(
        String(64),
        ForeignKey("network_flow_runs.id"),
        nullable=False,
        index=True,
    )

    status = Column(String(32), nullable=False, default="COMPLETED")
    objective_value = Column(Float, nullable=True)
    results_json = Column(Text, nullable=True)
    provenance = Column(Text, nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )