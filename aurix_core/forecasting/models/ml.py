import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, List, Tuple
from .base import BaseForecaster

try:
    import xgboost as xgb  # type: ignore

    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False

try:
    from sklearn.ensemble import RandomForestRegressor  # type: ignore

    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False


class MLFeatureEngineer:
    @staticmethod
    def create_features(y: pd.Series, freq: str = "D") -> Tuple[pd.DataFrame, pd.Series]:
        """Generates frequency-aware lag and rolling features while ensuring dynamic history safety."""
        df = pd.DataFrame({"target": y.copy()})
        n_obs = len(df)

        if freq in ["W", "W-SUN", "W-MON"]:
            candidate_lags = [1, 4, 13, 52]
            candidate_windows = [4, 13, 26]
        elif freq in ["M", "MS"]:
            candidate_lags = [1, 3, 6, 12]
            candidate_windows = [3, 6, 12]
        else:  # Daily default
            candidate_lags = [1, 7, 14]
            candidate_windows = [3, 7, 14, 30]

        valid_lags = [k for k in candidate_lags if (n_obs - k) >= 1]
        valid_windows = [w for w in candidate_windows if (n_obs - w) >= 1]

        if not valid_lags and n_obs >= 2:
            valid_lags = [1]

        for lag in valid_lags:
            df[f"lag_{lag}"] = df["target"].shift(lag)

        for w in valid_windows:
            df[f"rolling_mean_{w}"] = df["target"].shift(1).rolling(window=w, min_periods=1).mean().fillna(0.0)
            df[f"rolling_std_{w}"] = df["target"].shift(1).rolling(window=w, min_periods=1).std().fillna(0.0)

        if isinstance(df.index, pd.DatetimeIndex):
            df["month"] = df.index.month
            if freq in ["W", "W-SUN", "W-MON"]:
                df["week"] = df.index.isocalendar().week.astype(int)
            elif freq not in ["M", "MS"]:
                df["dayofweek"] = df.index.dayofweek
        else:
            df["month"] = 1

        df = df.dropna()
        if df.empty:
            return pd.DataFrame(), pd.Series(dtype=float)

        X = df.drop(columns=["target"])
        y_train = df["target"]
        return X, y_train


class XGBoostForecaster(BaseForecaster):
    def __init__(self, freq: str = "D", config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(model_id="XGBOOST", config=config)
        if not HAS_XGBOOST:
            raise ImportError("xgboost package is not installed.")
        self.freq = freq
        self.model = xgb.XGBRegressor(n_estimators=100, learning_rate=0.1, max_depth=4, random_state=42, verbosity=0)
        self.history_buffer: List[float] = []
        self.last_index_val: Any = None
        self.feature_names: List[str] = []

    def fit(self, y: pd.Series, X: Optional[pd.DataFrame] = None) -> "XGBoostForecaster":
        obs = y.dropna()
        if len(obs) < 3:
            raise ValueError("Insufficient history for XGBoost fit.")
        X_train, y_train = MLFeatureEngineer.create_features(obs, freq=self.freq)
        if len(X_train) < 1:
            raise ValueError("Insufficient training rows after feature engineering.")
        self.feature_names = list(X_train.columns)
        self.model.fit(X_train, y_train)
        self.history_buffer = [float(v) for v in obs.tolist()]
        self.last_index_val = obs.index[-1]
        self.is_fitted = True
        return self

    def predict(self, horizon: int, X_future: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction.")
        preds: List[float] = []
        current_history = list(self.history_buffer)
        for step in range(horizon):
            row_dict: Dict[str, float] = {}
            for col in self.feature_names:
                if col.startswith("lag_"):
                    lag_num = int(col.split("_")[1])
                    if len(current_history) >= lag_num:
                        row_dict[col] = current_history[-lag_num]
                    else:
                        row_dict[col] = current_history[-1]
                elif col.startswith("rolling_mean_"):
                    w_num = int(col.split("_")[2])
                    recent = current_history[-w_num:] if len(current_history) >= w_num else current_history
                    row_dict[col] = float(np.mean(recent)) if recent else 0.0
                elif col.startswith("rolling_std_"):
                    w_num = int(col.split("_")[2])
                    recent = current_history[-w_num:] if len(current_history) >= w_num else current_history
                    row_dict[col] = float(np.std(recent, ddof=0)) if len(recent) > 1 else 0.0
                elif col == "month":
                    row_dict[col] = 1.0
                elif col == "dayofweek":
                    row_dict[col] = 0.0
                elif col == "week":
                    row_dict[col] = 1.0

            x_pred = pd.DataFrame([row_dict], columns=self.feature_names)
            pred_val = float(self.model.predict(x_pred)[0])
            preds.append(pred_val)
            current_history.append(pred_val)

        return {
            "point_forecast": preds,
            "lower_bound": None,
            "upper_bound": None,
            "interval_status": "INTERVAL_NOT_AVAILABLE",
        }

    def get_params(self) -> Dict[str, Any]:
        return {
            "model_id": self.model_id,
            "freq": self.freq,
            "feature_names": self.feature_names,
            "n_estimators": 100,
            "learning_rate": 0.1,
            "max_depth": 4,
        }


class RandomForestForecaster(BaseForecaster):
    def __init__(self, freq: str = "D", config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(model_id="RANDOM_FOREST", config=config)
        if not HAS_SKLEARN:
            raise ImportError("scikit-learn package is not installed.")
        self.freq = freq
        self.model = RandomForestRegressor(n_estimators=100, max_depth=6, random_state=42)
        self.history_buffer: List[float] = []
        self.last_index_val: Any = None
        self.feature_names: List[str] = []

    def fit(self, y: pd.Series, X: Optional[pd.DataFrame] = None) -> "RandomForestForecaster":
        obs = y.dropna()
        if len(obs) < 3:
            raise ValueError("Insufficient history for Random Forest fit.")
        X_train, y_train = MLFeatureEngineer.create_features(obs, freq=self.freq)
        if len(X_train) < 1:
            raise ValueError("Insufficient training rows after feature engineering.")
        self.feature_names = list(X_train.columns)
        self.model.fit(X_train, y_train)
        self.history_buffer = [float(v) for v in obs.tolist()]
        self.last_index_val = obs.index[-1]
        self.is_fitted = True
        return self

    def predict(self, horizon: int, X_future: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction.")
        preds: List[float] = []
        current_history = list(self.history_buffer)
        for step in range(horizon):
            row_dict: Dict[str, float] = {}
            for col in self.feature_names:
                if col.startswith("lag_"):
                    lag_num = int(col.split("_")[1])
                    if len(current_history) >= lag_num:
                        row_dict[col] = current_history[-lag_num]
                    else:
                        row_dict[col] = current_history[-1]
                elif col.startswith("rolling_mean_"):
                    w_num = int(col.split("_")[2])
                    recent = current_history[-w_num:] if len(current_history) >= w_num else current_history
                    row_dict[col] = float(np.mean(recent)) if recent else 0.0
                elif col.startswith("rolling_std_"):
                    w_num = int(col.split("_")[2])
                    recent = current_history[-w_num:] if len(current_history) >= w_num else current_history
                    row_dict[col] = float(np.std(recent, ddof=0)) if len(recent) > 1 else 0.0
                elif col == "month":
                    row_dict[col] = 1.0
                elif col == "dayofweek":
                    row_dict[col] = 0.0
                elif col == "week":
                    row_dict[col] = 1.0

            x_pred = pd.DataFrame([row_dict], columns=self.feature_names)
            pred_val = float(self.model.predict(x_pred)[0])
            preds.append(pred_val)
            current_history.append(pred_val)

        return {
            "point_forecast": preds,
            "lower_bound": None,
            "upper_bound": None,
            "interval_status": "INTERVAL_NOT_AVAILABLE",
        }

    def get_params(self) -> Dict[str, Any]:
        return {
            "model_id": self.model_id,
            "freq": self.freq,
            "feature_names": self.feature_names,
            "n_estimators": 100,
            "max_depth": 6,
        }
