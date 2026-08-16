import pandas as pd
from typing import List, Optional, Tuple
from aurix_core.schema.phase4_contract import ForecastPoint
from aurix_core.forecasting.competition import ModelCompetitionEngine
from aurix_core.forecasting.models.base import BaseForecaster


class FinalForecastGenerator:
    """Retrains champion model on full history and generates production forecasts with provenance."""

    def __init__(self, horizon: int = 2) -> None:
        self.horizon = horizon
        self.competition_engine = ModelCompetitionEngine(horizon=horizon)

    def _generate_future_dates(self, last_date: pd.Timestamp, freq: str, horizon: int) -> List[str]:
        if freq == "D":
            future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=horizon, freq="D")
        elif freq in ["W", "W-SUN", "W-MON"]:
            future_dates = pd.date_range(start=last_date + pd.Timedelta(weeks=1), periods=horizon, freq="W")
        elif freq in ["M", "MS"]:
            future_dates = pd.date_range(start=last_date + pd.DateOffset(months=1), periods=horizon, freq="MS")
        else:
            future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=horizon, freq="D")

        return [str(d.date()) for d in future_dates]

    def generate(
        self, series: pd.Series, champion_model_id: Optional[str], freq: str
    ) -> Tuple[List[ForecastPoint], Optional[BaseForecaster], List[str]]:
        obs_series = series.dropna()
        if not champion_model_id or obs_series.empty or self.horizon <= 0:
            return [], None, ["target_series"]

        last_date = pd.to_datetime(obs_series.index[-1])
        future_dates = self._generate_future_dates(last_date, freq, self.horizon)

        try:
            factory = self.competition_engine._get_model_factory(champion_model_id, freq)
            champion_model: BaseForecaster = factory()
            champion_model.fit(obs_series)
            pred_dict = champion_model.predict(horizon=self.horizon)

            points = pred_dict.get("point_forecast", [])
            lowers = pred_dict.get("lower_bound", [None] * len(points))
            uppers = pred_dict.get("upper_bound", [None] * len(points))
            status = pred_dict.get("interval_status", "INTERVAL_NOT_AVAILABLE")

            if lowers is None or len(lowers) != len(points):
                lowers = [None] * len(points)
            if uppers is None or len(uppers) != len(points):
                uppers = [None] * len(points)

            feature_schema = getattr(champion_model, "feature_names", ["target_series"])

            forecast_points: List[ForecastPoint] = []
            for i, d_str in enumerate(future_dates):
                raw_val = float(points[i]) if i < len(points) else 0.0

                if raw_val < 0.0:
                    point_val = 0.0
                    constraint_applied = True
                    constraint_reason: Optional[str] = "NON_NEGATIVE_DEMAND"
                else:
                    point_val = raw_val
                    constraint_applied = False
                    constraint_reason = None

                low = float(lowers[i]) if (lowers and lowers[i] is not None) else None
                upp = float(uppers[i]) if (uppers and uppers[i] is not None) else None

                if low is not None:
                    low = max(0.0, low)
                if upp is not None:
                    upp = max(point_val, upp)

                forecast_points.append(
                    ForecastPoint(
                        date=d_str,
                        point_forecast=round(point_val, 2),
                        raw_model_forecast=round(raw_val, 2),
                        constraint_applied=constraint_applied,
                        constraint_reason=constraint_reason,
                        lower_bound=round(low, 2) if low is not None else None,
                        upper_bound=round(upp, 2) if upp is not None else None,
                        interval_status=status,
                    )
                )

            return forecast_points, champion_model, feature_schema

        except Exception:
            last_val = float(obs_series.iloc[-1]) if not obs_series.empty else 0.0
            fallback_points = [
                ForecastPoint(
                    date=d_str,
                    point_forecast=round(max(0.0, last_val), 2),
                    raw_model_forecast=round(last_val, 2),
                    constraint_applied=(last_val < 0.0),
                    constraint_reason="NON_NEGATIVE_DEMAND" if last_val < 0.0 else None,
                    lower_bound=None,
                    upper_bound=None,
                    interval_status="INTERVAL_NOT_AVAILABLE",
                )
                for d_str in future_dates
            ]
            return fallback_points, None, ["target_series"]
