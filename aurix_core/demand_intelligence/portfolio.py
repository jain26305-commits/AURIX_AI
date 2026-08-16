from typing import Dict, Any


class PortfolioAnalyzer:
    """Aggregates SKU intelligence into portfolio-level demand metrics."""

    @staticmethod
    def summarize(sku_intelligence: Dict[str, Any]) -> Dict[str, Any]:
        total_skus = len(sku_intelligence)
        class_dist: Dict[str, int] = {}
        for sku, data in sku_intelligence.items():
            cat = data.get("inferred_classification", {}).get("classification", "UNKNOWN")
            class_dist[cat] = class_dist.get(cat, 0) + 1

        return {"total_skus": total_skus, "classification_distribution": class_dist}
