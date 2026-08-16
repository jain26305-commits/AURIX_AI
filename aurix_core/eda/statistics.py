import pandas as pd
from typing import Dict, Any


class EDAStatistics:
    """Computes summary statistics for exploratory data analysis."""

    @staticmethod
    def compute(series: pd.Series) -> Dict[str, Any]:
        obs = series.dropna()
        if len(obs) == 0:
            return {"mean": 0.0, "std": 0.0, "min": 0.0, "max": 0.0}
        return {
            "mean": round(float(obs.mean()), 4),
            "std": round(float(obs.std()), 4) if len(obs) > 1 else 0.0,
            "min": round(float(obs.min()), 4),
            "max": round(float(obs.max()), 4),
        }
