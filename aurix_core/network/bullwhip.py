"""Bullwhip Effect variance amplification analyzer across multi-echelon time series."""

from typing import List, Optional
import numpy as np
from aurix_core.network.config import NetworkConfiguration
from aurix_core.schema.phase5_contract import TrackedValue, ValueState
from aurix_core.schema.phase8_contract import BullwhipMetrics


class BullwhipAnalyzer:
    """Calculates variance amplification ratios (Bullwhip Effect) between adjacent echelons with strict temporal alignment."""

    @classmethod
    def calculate_bullwhip_effect(
        cls,
        sku_id: str,
        echelon_pair: str,
        upstream_orders: List[float],
        downstream_demand: List[float],
        config: Optional[NetworkConfiguration] = None,
    ) -> BullwhipMetrics:
        cfg = config or NetworkConfiguration()

        n_up = len(upstream_orders)
        n_down = len(downstream_demand)

        # 1. Sample Size & Length Validation
        if n_up < cfg.min_bullwhip_sample_size or n_down < cfg.min_bullwhip_sample_size:
            unavail_tv = TrackedValue(
                value=None,
                state=ValueState.UNAVAILABLE,
                source="INSUFFICIENT_SAMPLE_SIZE",
            )
            return BullwhipMetrics(
                sku_id=sku_id,
                echelon_pair=echelon_pair,
                variance_upstream=0.0,
                variance_downstream=0.0,
                bullwhip_ratio=unavail_tv,
                status="NOT_ASSESSABLE",
                reason=f"Insufficient observations (n_up={n_up}, n_down={n_down}, min_required={cfg.min_bullwhip_sample_size}).",
            )

        if n_up != n_down:
            unavail_tv = TrackedValue(
                value=None,
                state=ValueState.UNAVAILABLE,
                source="TEMPORAL_MISMATCH",
            )
            return BullwhipMetrics(
                sku_id=sku_id,
                echelon_pair=echelon_pair,
                variance_upstream=0.0,
                variance_downstream=0.0,
                bullwhip_ratio=unavail_tv,
                status="NOT_ASSESSABLE",
                reason=f"Series length mismatch (n_up={n_up} vs n_down={n_down}). Requires explicit temporal alignment.",
            )

        # 2. Variance Calculations
        var_up = float(np.var(upstream_orders, ddof=1)) if n_up > 1 else 0.0
        var_down = float(np.var(downstream_demand, ddof=1)) if n_down > 1 else 0.0

        if var_down <= 0.0:
            unavail_tv = TrackedValue(
                value=None,
                state=ValueState.UNAVAILABLE,
                source="ZERO_DOWNSTREAM_VARIANCE",
            )
            return BullwhipMetrics(
                sku_id=sku_id,
                echelon_pair=echelon_pair,
                variance_upstream=round(var_up, 4),
                variance_downstream=round(var_down, 4),
                bullwhip_ratio=unavail_tv,
                status="NOT_ASSESSABLE",
                reason="Downstream demand variance is zero; Bullwhip ratio division by zero protection triggered.",
            )

        ratio_val = round(var_up / var_down, 4)
        is_amplified = ratio_val >= cfg.bullwhip_amplification_threshold

        ratio_tv = TrackedValue(
            value=ratio_val,
            state=ValueState.DERIVED,
            source="VARIANCE_AMPLIFICATION_CALCULATION",
        )

        return BullwhipMetrics(
            sku_id=sku_id,
            echelon_pair=echelon_pair,
            variance_upstream=round(var_up, 4),
            variance_downstream=round(var_down, 4),
            bullwhip_ratio=ratio_tv,
            status="BULLWHIP_AMPLIFIED" if is_amplified else "STABLE_VARIANCE",
            reason=f"Bullwhip ratio {ratio_val:.2f} {'exceeds' if is_amplified else 'below'} threshold {cfg.bullwhip_amplification_threshold:.2f}.",
        )
