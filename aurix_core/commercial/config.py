"""
AURIX Enterprise Sales & Commercial Intelligence — Tenant Commercial Configuration
Phase 22 Core Implementation.
Manages commercial rules: discount tolerances, dormancy thresholds, and OTIF criteria.
"""

from __future__ import annotations

from typing import Dict
from pydantic import BaseModel, Field


class TenantCommercialConfig(BaseModel):
    """Tenant-specific commercial parameters and governance thresholds."""
    tenant_id: str
    max_authorized_discount_pct: float = 10.0
    dormancy_threshold_days: int = 60
    churn_threshold_days: int = 120
    target_otif_pct: float = 95.0
    target_gross_margin_pct: float = 35.0
    pareto_a_threshold_pct: float = 80.0
    pareto_b_threshold_pct: float = 95.0


class CommercialConfigManager:
    """Manages tenant commercial configuration resolution."""

    _tenant_configs: Dict[str, TenantCommercialConfig] = {}

    @classmethod
    def get_config(cls, tenant_id: str) -> TenantCommercialConfig:
        """Retrieve tenant configuration or return standard default."""
        return cls._tenant_configs.get(
            tenant_id,
            TenantCommercialConfig(tenant_id=tenant_id),
        )

    @classmethod
    def set_config(cls, config: TenantCommercialConfig) -> None:
        """Store or update tenant commercial configuration."""
        cls._tenant_configs[config.tenant_id] = config
