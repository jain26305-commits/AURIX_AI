from typing import Dict


class InventoryConfiguration:
    """Centralized business configuration governing inventory policies and safe statistical mapping."""

    DEFAULT_SERVICE_LEVEL = 0.95
    DEFAULT_LEAD_TIME_DAYS = 14
    DEFAULT_REVIEW_PERIOD_DAYS = 1
    DEFAULT_HOLDING_COST_RATE = 0.20  # 20% annual holding cost
    DEFAULT_DAYS_IN_YEAR = 365

    @classmethod
    def get_z_score(cls, service_level: float) -> float:
        """Safe statistical mapping for Z-scores."""
        mapping: Dict[float, float] = {
            0.90: 1.282,
            0.95: 1.645,
            0.98: 2.054,
            0.99: 2.326,
            0.999: 3.090,
        }
        if service_level in mapping:
            return mapping[service_level]

        if service_level >= 0.999:
            return 3.090
        if service_level >= 0.99:
            return 2.326
        if service_level >= 0.98:
            return 2.054
        if service_level >= 0.95:
            return 1.645
        if service_level >= 0.90:
            return 1.282

        return 0.0
