import pandas as pd
from typing import Dict, Any, List


class ModelEligibilityGate:
    """Independently verifies whether Phase 2 model candidates are actually eligible to train."""

    @staticmethod
    def evaluate_eligibility(
        candidates: List[str],
        series: pd.Series,
        freq: str,
        missing_pct: float,
        demand_class: str,
        seasonal_detected: bool,
    ) -> Dict[str, Dict[str, Any]]:

        obs_series = series.dropna()
        n_obs = len(obs_series)

        eligibility_report: Dict[str, Dict[str, Any]] = {}

        all_candidates = set(candidates)
        all_candidates.update(["NAIVE", "MOVING_AVERAGE"])
        if seasonal_detected:
            all_candidates.add("SEASONAL_NAIVE")

        for model_id in all_candidates:
            eligible = True
            reason = "Eligible for competition."

            if n_obs < 2:
                eligible = False
                reason = "Insufficient history (less than 2 observations)."
            else:
                if model_id == "SEASONAL_NAIVE":
                    if not seasonal_detected or n_obs < 3:
                        eligible = False
                        reason = "Seasonality unsupported or history too short."

                elif model_id in ["ARIMA", "ETS"]:
                    if n_obs < 3:
                        eligible = False
                        reason = "Need at least 3 observations for statistical fitting."

                elif model_id == "SARIMA":
                    if not seasonal_detected or n_obs < 4:
                        eligible = False
                        reason = "SARIMA requires confirmed seasonality and history."

                elif model_id in ["CROSTON", "SBA"]:
                    if n_obs < 3:
                        eligible = False
                        reason = "Insufficient history for Croston/SBA."

                elif model_id in ["XGBOOST", "RANDOM_FOREST"]:
                    if n_obs < 4:
                        eligible = False
                        reason = "ML models require >= 4 observations."

            eligibility_report[model_id] = {"eligible": eligible, "reason": reason}

        return eligibility_report
