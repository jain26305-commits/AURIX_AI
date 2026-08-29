"""Audits dataset readiness and Phase 19 Canonical Data Fabric completeness."""

from typing import Any, Dict, List, Optional
import pandas as pd


class QualityReadinessAuditor:
    """Audits dataset readiness for demand forecasting and multi-domain data fabric."""

    @staticmethod
    def audit(df: pd.DataFrame, required_columns: List[str]) -> Dict[str, Any]:
        missing_cols = [col for col in required_columns if col not in df.columns]
        is_ready = len(missing_cols) == 0 and len(df) > 0
        return {"is_ready": is_ready, "missing_columns": missing_cols, "row_count": len(df)}

    @classmethod
    def evaluate_data_fabric_readiness(
        cls,
        datasets: Dict[str, pd.DataFrame],
    ) -> Dict[str, Any]:
        """Calculates portfolio-wide data fabric completeness score."""
        domain_requirements = {
            "products": ["sku_code"],
            "locations": ["location_name"],
            "inventory_positions": ["sku_id", "location_id", "on_hand"],
            "orders": ["order_number", "total_amount"],
        }

        modules_ready = 0
        total_modules = len(domain_requirements)
        details = {}

        for dom, reqs in domain_requirements.items():
            df = datasets.get(dom, pd.DataFrame())
            audit_res = cls.audit(df, reqs)
            details[dom] = audit_res
            if audit_res["is_ready"]:
                modules_ready += 1

        overall_score = round((modules_ready / total_modules) * 100.0, 1)
        return {
            "overall_platform_readiness_percent": overall_score,
            "ready_domains_count": modules_ready,
            "total_domains_count": total_modules,
            "domain_audits": details,
        }
