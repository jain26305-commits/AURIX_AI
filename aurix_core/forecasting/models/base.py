from abc import ABC, abstractmethod
import pandas as pd
from typing import Dict, Any, Optional


class BaseForecaster(ABC):
    """Abstract base class establishing the contract for all AURIX forecasters."""

    def __init__(self, model_id: str, config: Optional[Dict[str, Any]] = None) -> None:
        self.model_id = model_id
        self.config = config or {}
        self.is_fitted = False

    @abstractmethod
    def fit(self, y: pd.Series, X: Optional[pd.DataFrame] = None) -> "BaseForecaster":
        """Fits the forecaster using training time series y and optional exogenous features X."""
        pass

    @abstractmethod
    def predict(self, horizon: int, X_future: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """Generates point forecasts and prediction intervals."""
        pass

    @abstractmethod
    def get_params(self) -> Dict[str, Any]:
        """Returns model configuration parameters."""
        pass
