import numpy as np
import pandas as pd
from typing import Dict, Any


class DemandClassifier:
    """Classifies demand series into SMOOTH, ERRATIC, INTERMITTENT, or LUMPY using Syntetos-Boylan criteria."""

    @staticmethod
    def classify(series: pd.Series) -> Dict[str, Any]:
        obs = series.dropna().to_numpy(dtype=float)
        if len(obs) == 0:
            return {"classification": "INSUFFICIENT_DATA", "adi": None, "cv2": None}

        non_zero_indices = np.where(obs > 0)[0]
        if len(non_zero_indices) < 2:
            return {"classification": "INTERMITTENT", "adi": 2.0, "cv2": 0.0}

        intervals = np.diff(non_zero_indices)
        adi = float(np.mean(intervals))

        non_zero_vals = obs[non_zero_indices]
        mean_val = np.mean(non_zero_vals)
        std_val = np.std(non_zero_vals, ddof=1) if len(non_zero_vals) > 1 else 0.0
        cv2 = float((std_val / mean_val) ** 2) if mean_val > 0 else 0.0

        if adi < 1.32 and cv2 < 0.49:
            category = "SMOOTH"
        elif adi >= 1.32 and cv2 < 0.49:
            category = "INTERMITTENT"
        elif adi < 1.32 and cv2 >= 0.49:
            category = "ERRATIC"
        else:
            category = "LUMPY"

        return {"classification": category, "adi": round(adi, 4), "cv2": round(cv2, 4)}
