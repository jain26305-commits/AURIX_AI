import numpy as np
import pandas as pd
from typing import Dict, Union


class MetricsEngine:
    """Calculates forecasting performance metrics safely without silent NaNs."""

    @staticmethod
    def evaluate(actuals: pd.Series, predictions: pd.Series) -> Dict[str, Union[float, str]]:
        act = actuals.to_numpy(dtype=float)
        pred = predictions.to_numpy(dtype=float)

        if len(act) == 0 or len(pred) == 0 or len(act) != len(pred):
            return {
                "wape": "NOT_COMPUTABLE",
                "mae": "NOT_COMPUTABLE",
                "rmse": "NOT_COMPUTABLE",
                "bias": "NOT_COMPUTABLE",
            }

        mae = float(np.mean(np.abs(act - pred)))
        rmse = float(np.sqrt(np.mean((act - pred) ** 2)))

        sum_act = float(np.sum(np.abs(act)))
        if sum_act == 0.0:
            wape = 0.0 if np.sum(np.abs(pred)) == 0.0 else 1.0
        else:
            wape = float(np.sum(np.abs(act - pred)) / sum_act)

        sum_pred_minus_act = float(np.sum(pred - act))
        bias = 0.0 if sum_act == 0.0 else float(sum_pred_minus_act / sum_act)

        return {"wape": round(wape, 4), "mae": round(mae, 4), "rmse": round(rmse, 4), "bias": round(bias, 4)}
