import pandas as pd


class TemporalAligner:
    """Aligns time series onto a regular frequency grid."""

    @staticmethod
    def align(series: pd.Series, freq: str = "D") -> pd.Series:
        if series.empty:
            return series
        resampled = series.resample(freq).sum().fillna(0.0)
        return resampled
