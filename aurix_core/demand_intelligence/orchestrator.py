import pandas as pd
from typing import Dict, Any
from .classifier import DemandClassifier
from .forecastability import ForecastabilityEngine
from .portfolio import PortfolioAnalyzer


class Phase2Orchestrator:
    """Master controller for Phase 2 Demand Intelligence."""

    def __init__(self, canonical_df: pd.DataFrame) -> None:
        self.df = canonical_df

    def execute(self) -> Dict[str, Any]:
        sku_intelligence: Dict[str, Any] = {}

        for sku, group in self.df.groupby("sku_id"):
            series = group.set_index("date")["demand_qty"].sort_index()
            class_res = DemandClassifier.classify(series)
            datetime_index = pd.to_datetime(series.index)
            seasonal_detected = len(series) >= 14 and (datetime_index.dayofweek.nunique() > 1)
            forecastability = ForecastabilityEngine.evaluate(class_res, seasonal_detected)

            obs_data = [
                {
                    "date": str(idx),
                    "value": float(val),
                    "state": "OBSERVED_POSITIVE" if val > 0 else "OBSERVED_ZERO",
                }
                for idx, val in series.items()
            ]

            sku_intelligence[str(sku)] = {
                "entity_id": str(sku),
                "observed_data": obs_data,
                "data_quality": {"frequency": "D"},
                "missing_period_percentage": 0.0,
                "derived_metrics": {"volatility": {"cv2": class_res.get("cv2")}},
                "inferred_classification": {
                    "classification": class_res["classification"],
                    "seasonality": {"detected": seasonal_detected},
                },
                "model_candidates": forecastability["model_candidates"],
                "baseline_contract": "NAIVE",
                "limitations": [],
                "provenance": {"phase1_run_id": "RUN-1"},
            }

        portfolio_summary = PortfolioAnalyzer.summarize(sku_intelligence)
        return {
            "provenance": {"phase1_run_id": "RUN-1"},
            "portfolio_summary": portfolio_summary,
            "sku_intelligence": sku_intelligence,
        }
