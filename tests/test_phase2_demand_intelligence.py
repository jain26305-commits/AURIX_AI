import unittest
import pandas as pd
from aurix_core.demand_intelligence.classifier import DemandClassifier


class TestPhase2DemandIntelligence(unittest.TestCase):
    def test_smooth_classification(self) -> None:
        series = pd.Series([10.0, 11.0, 10.0, 12.0, 10.0, 11.0])
        res = DemandClassifier.classify(series)
        self.assertEqual(res["classification"], "SMOOTH")

    def test_intermittent_classification(self) -> None:
        series = pd.Series([0.0, 0.0, 10.0, 0.0, 0.0, 12.0])
        res = DemandClassifier.classify(series)
        self.assertEqual(res["classification"], "INTERMITTENT")
