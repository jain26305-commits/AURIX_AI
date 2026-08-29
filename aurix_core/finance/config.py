"""
AURIX Business Finance Intelligence — Tenant Financial Configuration
Phase 21 Core Implementation.
Manages tenant-specific fiscal calendars, reporting currencies, and thresholds.
"""

from __future__ import annotations

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class TenantFinanceConfig(BaseModel):
    """Tenant-level financial operating parameters."""
    tenant_id: str
    fiscal_year_start_month: int = 1  # 1 for Jan-Dec, 4 for Apr-Mar (India)
    base_currency: str = "USD"
    reporting_currency: str = "USD"
    annual_holding_cost_rate: float = 0.22  # 22% standard holding cost
    aging_buckets_days: List[int] = Field(default_factory=lambda: [30, 60, 90])
    materiality_threshold_pct: float = 2.0  # 2% variance materiality
    anomaly_z_score_threshold: float = 2.5
    margin_drop_alert_pct: float = 10.0


class FinanceConfigManager:
    """Manages tenant configuration resolution."""

    _tenant_configs: Dict[str, TenantFinanceConfig] = {}

    @classmethod
    def get_config(cls, tenant_id: str) -> TenantFinanceConfig:
        """Retrieve tenant configuration or return standard default."""
        return cls._tenant_configs.get(
            tenant_id,
            TenantFinanceConfig(tenant_id=tenant_id),
        )

    @classmethod
    def set_config(cls, config: TenantFinanceConfig) -> None:
        """Store or update tenant configuration."""
        cls._tenant_configs[config.tenant_id] = config
