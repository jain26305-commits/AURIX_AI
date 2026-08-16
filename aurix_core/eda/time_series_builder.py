import pandas as pd


class TimeSeriesBuilder:
    """Resamples and formats transaction records into regular time series."""

    @staticmethod
    def build(df: pd.DataFrame, date_col: str, qty_col: str, freq: str = "D") -> pd.Series:
        temp_df = df.copy()
        temp_df[date_col] = pd.to_datetime(temp_df[date_col])
        series = temp_df.set_index(date_col)[qty_col].resample(freq).sum().fillna(0.0)
        return series
