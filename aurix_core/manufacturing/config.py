"""
AURIX Manufacturing & Production Intelligence — Tenant Manufacturing Configuration
Phase 23 Core Implementation.
Manages plant parameters: shift hours, scrap tolerances, and bottleneck thresholds.
"""

from __future__ import annotations

from typing import Dict
from pydantic import BaseModel, Field


class TenantManufacturingConfig(BaseModel):
    """Tenant-specific plant operating parameters."""
    tenant_id: str
    standard_shift_hours: float = 8.0
    shifts_per_day: int = 2
    operating_days_per_month: int = 26
    planned_oee_target_pct: float = 85.0
    scrap_tolerance_pct: float = 3.0
    bottleneck_utilization_threshold_pct: float = 90.0
    max_bom_explosion_depth: int = 10


class ManufacturingConfigManager:
    """Manages tenant manufacturing configuration resolution."""

    _tenant_configs: Dict[str, TenantManufacturingConfig] = {}

    @classmethod
    def get_config(cls, tenant_id: str) -> TenantManufacturingConfig:
        """Retrieve tenant configuration or return standard default."""
        return cls._tenant_configs.get(
            tenant_id,
            TenantManufacturingConfig(tenant_id=tenant_id),
        )

    @classmethod
    def set_config(cls, config: TenantManufacturingConfig) -> None:
        """Store or update tenant manufacturing configuration."""
        cls._tenant_configs[config.tenant_id] = config
