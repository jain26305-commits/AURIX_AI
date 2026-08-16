import pandas as pd
from typing import Dict, Any


class DataProfiler:
    """Profiles datasets for completeness, row counts, and missing value ratios."""

    @staticmethod
    def profile(df: pd.DataFrame) -> Dict[str, Any]:
        total_rows = len(df)
        total_cols = len(df.columns)
        null_counts = df.isnull().sum().to_dict()
        return {
            "total_rows": total_rows,
            "total_columns": total_cols,
            "null_counts": {k: int(v) for k, v in null_counts.items()},
            "completeness_score": float(1.0 - (df.isnull().sum().sum() / max(1, total_rows * total_cols))),
        }
