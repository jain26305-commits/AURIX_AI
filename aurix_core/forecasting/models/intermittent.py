import numpy as np
import pandas as pd
from typing import Dict, Any, Optional
from .base import BaseForecaster


class CrostonForecaster(BaseForecaster):
    def __init__(self, alpha: float = 0.1, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(model_id="CROSTON", config=config)
        self.alpha = alpha
        self.forecast_val = 0.0

    def fit(self, y: pd.Series, X: Optional[pd.DataFrame] = None) -> "CrostonForecaster":
        obs = y.dropna().to_numpy(dtype=float)
        if len(obs) == 0:
            self.forecast_val = 0.0
            self.is_fitted = True
            return self
        non_zero_indices = np.where(obs > 0)[0]
        if len(non_zero_indices) == 0:
            self.forecast_val = 0.0
            self.is_fitted = True
            return self
        demand_sizes = obs[non_zero_indices]
        intervals = []
        prev_idx = -1
        for idx in non_zero_indices:
            intervals.append(float(int(idx) - prev_idx))
            prev_idx = int(idx)
        z = demand_sizes[0]
        p = intervals[0]
        for i in range(1, len(demand_sizes)):
            z = self.alpha * demand_sizes[i] + (1 - self.alpha) * z
            p = self.alpha * intervals[i] + (1 - self.alpha) * p
        self.forecast_val = float(z / p) if p > 0 else 0.0
        self.is_fitted = True
        return self

    def predict(self, horizon: int, X_future: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction.")
        preds = [self.forecast_val] * horizon
        return {
            "point_forecast": preds,
            "lower_bound": None,
            "upper_bound": None,
            "interval_status": "INTERVAL_NOT_AVAILABLE",
        }

    def get_params(self) -> Dict[str, Any]:
        return {"model_id": self.model_id, "alpha": self.alpha}


class SBAForecaster(BaseForecaster):
    def __init__(self, alpha: float = 0.1, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(model_id="SBA", config=config)
        self.alpha = alpha
        self.forecast_val = 0.0

    def fit(self, y: pd.Series, X: Optional[pd.DataFrame] = None) -> "SBAForecaster":
        obs = y.dropna().to_numpy(dtype=float)
        if len(obs) == 0:
            self.forecast_val = 0.0
            self.is_fitted = True
            return self
        non_zero_indices = np.where(obs > 0)[0]
        if len(non_zero_indices) == 0:
            self.forecast_val = 0.0
            self.is_fitted = True
            return self
        demand_sizes = obs[non_zero_indices]
        intervals = []
        prev_idx = -1
        for idx in non_zero_indices:
            intervals.append(float(int(idx) - prev_idx))
            prev_idx = int(idx)
        z = demand_sizes[0]
        p = intervals[0]
        for i in range(1, len(demand_sizes)):
            z = self.alpha * demand_sizes[i] + (1 - self.alpha) * z
            p = self.alpha * intervals[i] + (1 - self.alpha) * p
        correction_factor = 1.0 - (self.alpha / 2.0)
        base_croston = (z / p) if p > 0 else 0.0
        self.forecast_val = float(correction_factor * base_croston)
        self.is_fitted = True
        return self

    def predict(self, horizon: int, X_future: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction.")
        preds = [self.forecast_val] * horizon
        return {
            "point_forecast": preds,
            "lower_bound": None,
            "upper_bound": None,
            "interval_status": "INTERVAL_NOT_AVAILABLE",
        }

    def get_params(self) -> Dict[str, Any]:
        return {"model_id": self.model_id, "alpha": self.alpha}
