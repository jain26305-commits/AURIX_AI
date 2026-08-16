import pandas as pd
from typing import Dict, Any, List
from .registry import EvaluationStatus
from .backtest import RollingBacktester
from .models.baselines import NaiveForecaster, MovingAverageForecaster, SeasonalNaiveForecaster
from .models.statistical import ARIMAForecaster, SARIMAForecaster, ETSForecaster
from .models.intermittent import CrostonForecaster, SBAForecaster
from .models.ml import XGBoostForecaster, RandomForestForecaster


class ModelCompetitionEngine:
    """Executes model competition across eligible candidates using rolling backtests."""

    def __init__(self, horizon: int = 2, n_folds: int = 1, min_train_size: int = 3) -> None:
        self.backtester = RollingBacktester(min_train_size=min_train_size, horizon=horizon, n_folds=n_folds)

    def _get_model_factory(self, model_id: str, freq: str) -> Any:
        if model_id == "NAIVE":
            return lambda: NaiveForecaster()
        elif model_id == "MOVING_AVERAGE":
            return lambda: MovingAverageForecaster(window=3)
        elif model_id == "SEASONAL_NAIVE":
            period = 12 if freq in ["M", "MS"] else (52 if freq in ["W", "W-SUN", "W-MON"] else 7)
            return lambda: SeasonalNaiveForecaster(seasonal_period=period)
        elif model_id == "ARIMA":
            return lambda: ARIMAForecaster(order=(1, 1, 1))
        elif model_id == "SARIMA":
            period = 12 if freq in ["M", "MS"] else 7
            return lambda: SARIMAForecaster(order=(1, 1, 1), seasonal_order=(1, 1, 1, period))
        elif model_id == "ETS":
            period = 12 if freq in ["M", "MS"] else 7
            return lambda: ETSForecaster(seasonal="add", seasonal_periods=period)
        elif model_id == "CROSTON":
            return lambda: CrostonForecaster()
        elif model_id == "SBA":
            return lambda: SBAForecaster()
        elif model_id == "XGBOOST":
            return lambda: XGBoostForecaster(freq=freq)
        elif model_id == "RANDOM_FOREST":
            return lambda: RandomForestForecaster(freq=freq)
        else:
            raise ValueError(f"Unknown model identifier: {model_id}")

    def compete(
        self, series: pd.Series, eligibility_report: Dict[str, Dict[str, Any]], freq: str
    ) -> List[Dict[str, Any]]:

        competition_results: List[Dict[str, Any]] = []

        for model_id, report in eligibility_report.items():
            if not report["eligible"]:
                competition_results.append(
                    {
                        "model_id": model_id,
                        "status": EvaluationStatus.INELIGIBLE,
                        "reason": report["reason"],
                        "folds_tested": 0,
                        "wape": None,
                        "mae": None,
                        "rmse": None,
                        "bias": None,
                        "stability_variance": None,
                        "baseline_improvement_pct": None,
                    }
                )
                continue

            try:
                factory = self._get_model_factory(model_id, freq)
                backtest_res = self.backtester.run(series, factory)

                status = backtest_res.get("status", EvaluationStatus.EVALUATED)
                reason_str = (
                    "Evaluated successfully via rolling backtest." if status == "EVALUATED" else "Model failed."
                )

                competition_results.append(
                    {
                        "model_id": model_id,
                        "status": status,
                        "reason": reason_str,
                        "folds_tested": backtest_res.get("folds_tested", 0),
                        "wape": backtest_res.get("wape"),
                        "mae": backtest_res.get("mae"),
                        "rmse": backtest_res.get("rmse"),
                        "bias": backtest_res.get("bias"),
                        "stability_variance": backtest_res.get("stability_variance"),
                        "baseline_improvement_pct": None,
                    }
                )
            except Exception as e:
                competition_results.append(
                    {
                        "model_id": model_id,
                        "status": EvaluationStatus.MODEL_FAILED,
                        "reason": f"Execution crashed: {str(e)}",
                        "folds_tested": 0,
                        "wape": None,
                        "mae": None,
                        "rmse": None,
                        "bias": None,
                        "stability_variance": None,
                        "baseline_improvement_pct": None,
                    }
                )

        return competition_results
