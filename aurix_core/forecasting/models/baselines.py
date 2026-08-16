import pandas as pd
from typing import Dict, Any, Optional, List
from .base import BaseForecaster


class NaiveForecaster(BaseForecaster):
    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(model_id="NAIVE", config=config)
        self.last_val = 0.0

    def fit(self, y: pd.Series, X: Optional[pd.DataFrame] = None) -> "NaiveForecaster":
        obs = y.dropna()
        self.last_val = float(obs.iloc[-1]) if len(obs) > 0 else 0.0
        self.is_fitted = True
        return self

    def predict(self, horizon: int, X_future: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction.")
        preds = [self.last_val] * horizon
        return {
            "point_forecast": preds,
            "lower_bound": None,
            "upper_bound": None,
            "interval_status": "INTERVAL_NOT_AVAILABLE",
        }

    def get_params(self) -> Dict[str, Any]:
        return {"model_id": self.model_id}


class MovingAverageForecaster(BaseForecaster):
    def __init__(self, window: int = 3, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(model_id="MOVING_AVERAGE", config=config)
        self.window = window
        self.ma_val = 0.0

    def fit(self, y: pd.Series, X: Optional[pd.DataFrame] = None) -> "MovingAverageForecaster":
        obs = y.dropna()
        if len(obs) == 0:
            self.ma_val = 0.0
        else:
            w = min(self.window, len(obs))
            self.ma_val = float(obs.iloc[-w:].mean())
        self.is_fitted = True
        return self

    def predict(self, horizon: int, X_future: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction.")
        preds = [self.ma_val] * horizon
        return {
            "point_forecast": preds,
            "lower_bound": None,
            "upper_bound": None,
            "interval_status": "INTERVAL_NOT_AVAILABLE",
        }

    def get_params(self) -> Dict[str, Any]:
        return {"model_id": self.model_id, "window": self.window}


class SeasonalNaiveForecaster(BaseForecaster):
    def __init__(self, seasonal_period: int = 12, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(model_id="SEASONAL_NAIVE", config=config)
        self.period = seasonal_period
        self.history: List[float] = []

    def fit(self, y: pd.Series, X: Optional[pd.DataFrame] = None) -> "SeasonalNaiveForecaster":
        obs = y.dropna()
        self.history = [float(v) for v in obs.tolist()]
        self.is_fitted = True
        return self

    def predict(self, horizon: int, X_future: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction.")
        preds: List[float] = []
        hist_len = len(self.history)
        for i in range(horizon):
            lookback_idx = hist_len - self.period + (i % self.period)
            if 0 <= lookback_idx < hist_len:
                preds.append(self.history[lookback_idx])
            elif hist_len > 0:
                preds.append(self.history[-1])
            else:
                preds.append(0.0)
        return {
            "point_forecast": preds,
            "lower_bound": None,
            "upper_bound": None,
            "interval_status": "INTERVAL_NOT_AVAILABLE",
        }

    def get_params(self) -> Dict[str, Any]:
        return {"model_id": self.model_id, "seasonal_period": self.period}
