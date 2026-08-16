import pandas as pd
from typing import Dict, Any, Optional
from statsmodels.tsa.arima.model import ARIMA  # type: ignore
from statsmodels.tsa.holtwinters import ExponentialSmoothing  # type: ignore
from .base import BaseForecaster


class ARIMAForecaster(BaseForecaster):
    def __init__(self, order: tuple[int, int, int] = (1, 1, 1), config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(model_id="ARIMA", config=config)
        self.order = order
        self._fitted_model = None

    def fit(self, y: pd.Series, X: Optional[pd.DataFrame] = None) -> "ARIMAForecaster":
        obs = y.dropna()
        if len(obs) < max(sum(self.order), 3):
            raise ValueError("Insufficient history for ARIMA fit.")
        if obs.nunique() <= 1:
            raise ValueError("Constant series detected; ARIMA not suitable.")
        try:
            model = ARIMA(obs, order=self.order, enforce_stationarity=False, enforce_invertibility=False)
            self._fitted_model = model.fit()
            self.is_fitted = True
        except Exception as e:
            raise RuntimeError(f"ARIMA fitting failed: {str(e)}")
        return self

    def predict(self, horizon: int, X_future: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        if not self.is_fitted or self._fitted_model is None:
            raise ValueError("Model must be fitted before prediction.")
        try:
            forecast_result = self._fitted_model.get_forecast(steps=horizon)
            pred_mean = forecast_result.predicted_mean.tolist()
            ci = forecast_result.conf_int(alpha=0.05)
            lower = ci.iloc[:, 0].tolist() if not ci.empty else None
            upper = ci.iloc[:, 1].tolist() if not ci.empty else None
            return {
                "point_forecast": [float(v) for v in pred_mean],
                "lower_bound": [float(v) for v in lower] if lower else None,
                "upper_bound": [float(v) for v in upper] if upper else None,
                "interval_status": "COMPUTED",
            }
        except Exception as e:
            raise RuntimeError(f"ARIMA prediction failed: {str(e)}")

    def get_params(self) -> Dict[str, Any]:
        return {"model_id": self.model_id, "order": self.order}


class SARIMAForecaster(BaseForecaster):
    def __init__(
        self,
        order: tuple[int, int, int] = (1, 1, 1),
        seasonal_order: tuple[int, int, int, int] = (1, 1, 1, 12),
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(model_id="SARIMA", config=config)
        self.order = order
        self.seasonal_order = seasonal_order
        self._fitted_model = None

    def fit(self, y: pd.Series, X: Optional[pd.DataFrame] = None) -> "SARIMAForecaster":
        obs = y.dropna()
        s_period = self.seasonal_order[3]
        if len(obs) < (s_period * 2):
            raise ValueError(f"Insufficient history for SARIMA with seasonal period {s_period}.")
        if obs.nunique() <= 1:
            raise ValueError("Constant series detected; SARIMA not suitable.")
        try:
            model = ARIMA(
                obs,
                order=self.order,
                seasonal_order=self.seasonal_order,
                enforce_stationarity=False,
                enforce_invertibility=False,
            )
            self._fitted_model = model.fit()
            self.is_fitted = True
        except Exception as e:
            raise RuntimeError(f"SARIMA fitting failed: {str(e)}")
        return self

    def predict(self, horizon: int, X_future: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        if not self.is_fitted or self._fitted_model is None:
            raise ValueError("Model must be fitted before prediction.")
        try:
            forecast_result = self._fitted_model.get_forecast(steps=horizon)
            pred_mean = forecast_result.predicted_mean.tolist()
            ci = forecast_result.conf_int(alpha=0.05)
            lower = ci.iloc[:, 0].tolist() if not ci.empty else None
            upper = ci.iloc[:, 1].tolist() if not ci.empty else None
            return {
                "point_forecast": [float(v) for v in pred_mean],
                "lower_bound": [float(v) for v in lower] if lower else None,
                "upper_bound": [float(v) for v in upper] if upper else None,
                "interval_status": "COMPUTED",
            }
        except Exception as e:
            raise RuntimeError(f"SARIMA prediction failed: {str(e)}")

    def get_params(self) -> Dict[str, Any]:
        return {"model_id": self.model_id, "order": self.order, "seasonal_order": self.seasonal_order}


class ETSForecaster(BaseForecaster):
    def __init__(
        self,
        seasonal: Optional[str] = None,
        seasonal_periods: Optional[int] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(model_id="ETS", config=config)
        self.seasonal = seasonal
        self.seasonal_periods = seasonal_periods
        self._fitted_model = None

    def fit(self, y: pd.Series, X: Optional[pd.DataFrame] = None) -> "ETSForecaster":
        obs = y.dropna()
        if len(obs) < 4:
            raise ValueError("Insufficient history for ETS fit.")
        if obs.nunique() <= 1:
            raise ValueError("Constant series detected; ETS trivial.")
        try:
            use_seasonal = self.seasonal if (self.seasonal_periods and len(obs) >= self.seasonal_periods * 2) else None
            s_periods = self.seasonal_periods if use_seasonal else None
            model = ExponentialSmoothing(
                obs, trend="add", seasonal=use_seasonal, seasonal_periods=s_periods, initialization_method="estimated"
            )
            self._fitted_model = model.fit(optimized=True)
            self.is_fitted = True
        except Exception:
            try:
                model = ExponentialSmoothing(obs, initialization_method="estimated")
                self._fitted_model = model.fit(optimized=True)
                self.is_fitted = True
            except Exception as inner_e:
                raise RuntimeError(f"ETS fitting failed completely: {str(inner_e)}")
        return self

    def predict(self, horizon: int, X_future: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        if not self.is_fitted or self._fitted_model is None:
            raise ValueError("Model must be fitted before prediction.")
        try:
            preds = self._fitted_model.forecast(steps=horizon)
            pred_list = preds.tolist() if hasattr(preds, "tolist") else list(preds)
            return {
                "point_forecast": [float(v) for v in pred_list],
                "lower_bound": None,
                "upper_bound": None,
                "interval_status": "INTERVAL_NOT_AVAILABLE",
            }
        except Exception as e:
            raise RuntimeError(f"ETS prediction failed: {str(e)}")

    def get_params(self) -> Dict[str, Any]:
        return {"model_id": self.model_id, "seasonal": self.seasonal, "seasonal_periods": self.seasonal_periods}
