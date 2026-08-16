import pandas as pd
from typing import Dict, Any, List, Callable
from .metrics import MetricsEngine


class RollingBacktester:
    """Executes chronological rolling-origin (walk-forward) backtesting to prevent leakage."""

    def __init__(self, min_train_size: int = 3, horizon: int = 2, n_folds: int = 1) -> None:
        self.min_train_size = min_train_size
        self.horizon = horizon
        self.n_folds = n_folds

    def run(self, series: pd.Series, model_factory: Callable[[], Any]) -> Dict[str, Any]:
        obs_series = series.dropna()
        total_len = len(obs_series)

        effective_min_train = min(self.min_train_size, max(1, total_len - self.horizon))

        if total_len < (effective_min_train + self.horizon):
            return {
                "status": "INSUFFICIENT_HISTORY_FOR_BACKTEST",
                "folds_tested": 0,
                "wape": None,
                "mae": None,
                "rmse": None,
                "bias": None,
                "stability_variance": 0.0,
                "fold_scores": [],
            }

        max_possible_starts = total_len - effective_min_train - self.horizon + 1
        folds_to_run = min(self.n_folds, max_possible_starts)

        if folds_to_run <= 0:
            folds_to_run = 1

        fold_metrics_list: List[Dict[str, Any]] = []

        step = max(1, (total_len - effective_min_train - self.horizon) // max(1, folds_to_run))
        start_indices = [total_len - self.horizon - (i * step) for i in range(folds_to_run)]
        start_indices = sorted(list(set(start_indices)))

        for train_end_idx in start_indices:
            if train_end_idx < effective_min_train:
                train_end_idx = effective_min_train

            train_data = obs_series.iloc[:train_end_idx]
            test_data = obs_series.iloc[train_end_idx : train_end_idx + self.horizon]

            if len(test_data) == 0:
                continue

            try:
                model = model_factory()
                model.fit(train_data)
                preds_dict = model.predict(horizon=len(test_data))
                point_preds = pd.Series(preds_dict["point_forecast"], index=test_data.index)

                fold_res = MetricsEngine.evaluate(test_data, point_preds)
                fold_metrics_list.append(fold_res)
            except Exception as e:
                fold_metrics_list.append({"error": str(e), "wape": "NOT_COMPUTABLE"})

        valid_wapes = [float(f["wape"]) for f in fold_metrics_list if isinstance(f.get("wape"), (int, float))]
        valid_maes = [float(f["mae"]) for f in fold_metrics_list if isinstance(f.get("mae"), (int, float))]
        valid_rmses = [float(f["rmse"]) for f in fold_metrics_list if isinstance(f.get("rmse"), (int, float))]
        valid_biases = [float(f["bias"]) for f in fold_metrics_list if isinstance(f.get("bias"), (int, float))]

        avg_wape = float(sum(valid_wapes) / len(valid_wapes)) if valid_wapes else None
        avg_mae = float(sum(valid_maes) / len(valid_maes)) if valid_maes else None
        avg_rmse = float(sum(valid_rmses) / len(valid_rmses)) if valid_rmses else None
        avg_bias = float(sum(valid_biases) / len(valid_biases)) if valid_biases else None

        stability_var = float(pd.Series(valid_wapes).var(ddof=0)) if len(valid_wapes) > 1 else 0.0

        status_str = "EVALUATED" if valid_wapes else "MODEL_FAILED"
        return {
            "status": status_str,
            "folds_tested": len(fold_metrics_list),
            "wape": avg_wape,
            "mae": avg_mae,
            "rmse": avg_rmse,
            "bias": avg_bias,
            "stability_variance": round(stability_var, 5),
            "fold_scores": fold_metrics_list,
        }
