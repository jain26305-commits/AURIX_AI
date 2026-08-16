from typing import Dict, Any


class ForecastabilityEngine:
    """Evaluates series forecastability and recommends eligible model candidates."""

    @staticmethod
    def evaluate(classification_res: Dict[str, Any], seasonal_detected: bool) -> Dict[str, Any]:
        cat = classification_res.get("classification", "SMOOTH")

        if cat == "SMOOTH":
            candidates = ["NAIVE", "MOVING_AVERAGE", "ARIMA", "ETS", "XGBOOST", "RANDOM_FOREST"]
        elif cat == "ERRATIC":
            candidates = ["NAIVE", "MOVING_AVERAGE", "ETS", "XGBOOST", "RANDOM_FOREST"]
        elif cat in ["INTERMITTENT", "LUMPY"]:
            candidates = ["NAIVE", "CROSTON", "SBA"]
        else:
            candidates = ["NAIVE"]

        if seasonal_detected and cat not in ["INTERMITTENT", "LUMPY"]:
            candidates.extend(["SEASONAL_NAIVE", "SARIMA"])

        return {"model_candidates": list(set(candidates)), "is_forecastable": cat != "INSUFFICIENT_DATA"}
