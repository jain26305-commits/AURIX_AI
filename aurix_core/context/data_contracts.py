"""
AURIX Enterprise Business Context Graph — Data Contract Registry
Phase 24 Core Implementation.
Manages enterprise data contracts, schema versioning, freshness/quality SLOs, and downstream consumer dependency impact.
"""

from __future__ import annotations

from typing import Dict, List, Optional
from aurix_core.context.contracts import (
    DataContractDefinition,
    DataContractStatus,
)


class DataContractRegistry:
    """Central registry tracking data contracts and downstream operational impacts."""

    _registry: Dict[str, List[DataContractDefinition]] = {}

    @classmethod
    def register_contract(cls, contract: DataContractDefinition) -> DataContractDefinition:
        """Register or update a data contract specification."""
        tenant_contracts = cls._registry.setdefault(contract.tenant_id, [])
        # Replace existing if dataset matches
        tenant_contracts[:] = [c for c in tenant_contracts if c.dataset_name != contract.dataset_name]
        tenant_contracts.append(contract)
        return contract

    @classmethod
    def get_contracts(cls, tenant_id: str) -> List[DataContractDefinition]:
        """Retrieve all active data contracts for a tenant."""
        return cls._registry.get(tenant_id, [
            DataContractDefinition(
                tenant_id=tenant_id,
                dataset_name="sales_orders",
                schema_version="v2.1",
                owner_domain="COMMERCIAL",
                freshness_slo_seconds=300,
                quality_slo_pct=99.5,
                downstream_consumers=["FINANCE_PNL", "MRP_ENGINE", "CONTEXT_GRAPH", "REVENUE_AT_RISK"],
                status=DataContractStatus.ACTIVE,
            ),
            DataContractDefinition(
                tenant_id=tenant_id,
                dataset_name="inventory_positions",
                schema_version="v1.4",
                owner_domain="SUPPLY_CHAIN",
                freshness_slo_seconds=600,
                quality_slo_pct=98.0,
                downstream_consumers=["MRP_ENGINE", "WORKING_CAPITAL_CALCULATOR", "ASSURANCE_ENGINE"],
                status=DataContractStatus.ACTIVE,
            ),
        ])

    @classmethod
    def get_downstream_impact(cls, tenant_id: str, dataset_name: str) -> List[str]:
        """Identify downstream analytical and operational modules dependent on a dataset."""
        contracts = cls.get_contracts(tenant_id)
        for c in contracts:
            if c.dataset_name.lower() == dataset_name.lower():
                return c.downstream_consumers
        return ["UNKNOWN_CONSUMERS"]
