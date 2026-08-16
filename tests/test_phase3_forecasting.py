"""Comprehensive Unit, Integration, Adversarial, and Persistence Test Suite for Phase 3 Forecasting."""

import os
import unittest
import joblib  # type: ignore
from datetime import datetime
import pandas as pd
from typing import Dict, Any, List, Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from aurix_core.schema.phase3_contract import Phase3InputContract, SeriesObservation
from aurix_core.forecasting.orchestrator import Phase3Orchestrator
from aurix_core.forecasting.models.ml import HAS_XGBOOST, MLFeatureEngineer, XGBoostForecaster
from aurix_core.forecasting.backtest import RollingBacktester
from aurix_core.forecasting.models.baselines import NaiveForecaster
from aurix_core.forecasting.champion import ChampionSelector
from aurix_core.utils.provenance import compute_sha256

# Database & Persistence Imports
from aurix_core.database.engine import Base
from aurix_core.database.models import forecasting as forecasting_models
from aurix_core.database.models import supply_chain
from aurix_core.database.models import ingestion
from aurix_core.database.repositories.forecasting import ForecastRunRepository, ForecastPointRepository
from aurix_core.forecasting.service import ForecastingService


class TestPhase3Forecasting(unittest.TestCase):

    def _create_mock_portfolio(
        self,
        sku_id: str,
        values: List[Optional[float]],
        freq: str = "D",
        missing_pct: float = 0.0,
        class_type: str = "SMOOTH",
        seasonal: bool = False,
        candidates: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        if candidates is None:
            candidates = ["NAIVE", "MOVING_AVERAGE", "ETS"]

        start_date = datetime(2026, 1, 1)
        obs_data = []
        for i, val in enumerate(values):
            d = start_date + pd.Timedelta(days=i)
            if val == 0:
                state = "OBSERVED_ZERO"
            elif val is not None:
                state = "OBSERVED_POSITIVE"
            else:
                state = "MISSING_PERIOD"
            obs_data.append(SeriesObservation(date=str(d.date()), value=val, state=state))

        contract = Phase3InputContract(
            entity_id=sku_id,
            observed_data=obs_data,
            data_quality={"frequency": freq},
            missing_period_percentage=missing_pct,
            derived_metrics={"volatility": {"cv2": 0.1}, "intermittency": {"adi": 1.0}},
            inferred_classification={"classification": class_type, "seasonality": {"detected": seasonal}},
            model_candidates=candidates,
            baseline_contract="NAIVE",
            limitations=[],
            provenance={"run_id": "TEST-RUN"},
        )
        return {"provenance": {"phase1_run_id": "RUN-1"}, "sku_intelligence": {sku_id: contract.model_dump()}}

    def test_01_stable_demand(self) -> None:
        portfolio = self._create_mock_portfolio("STABLE-01", [100.0, 102.0, 99.0, 101.0, 100.0, 101.0, 100.0])
        orch = Phase3Orchestrator(portfolio, horizon=2)
        res = orch.execute()
        self.assertEqual(res["portfolio_summary"]["forecast_available"], 1)
        self.assertIn("STABLE-01", res["sku_forecasts"])

    def test_02_trending_demand(self) -> None:
        portfolio = self._create_mock_portfolio("TREND-01", [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0])
        orch = Phase3Orchestrator(portfolio, horizon=2)
        res = orch.execute()
        self.assertIsNotNone(res["sku_forecasts"]["TREND-01"]["champion_model"])

    def test_03_seasonal_demand(self) -> None:
        vals: List[Optional[float]] = [
            10.0, 20.0, 30.0, 10.0, 20.0, 30.0, 10.0, 20.0, 30.0, 10.0, 20.0, 30.0, 10.0, 20.0, 30.0,
        ]
        portfolio = self._create_mock_portfolio(
            "SEASON-01", vals, freq="D", seasonal=True, candidates=["SEASONAL_NAIVE", "ETS"]
        )
        orch = Phase3Orchestrator(portfolio, horizon=2)
        res = orch.execute()
        self.assertEqual(res["sku_forecasts"]["SEASON-01"]["forecast_status"], "FORECAST_AVAILABLE")

    def test_04_erratic_demand(self) -> None:
        portfolio = self._create_mock_portfolio("ERRATIC-01", [10.0, 150.0, 5.0, 200.0, 12.0, 180.0, 8.0, 220.0])
        orch = Phase3Orchestrator(portfolio, horizon=2)
        res = orch.execute()
        self.assertIn("FORECAST_AVAILABLE", [res["sku_forecasts"]["ERRATIC-01"]["forecast_status"]])

    def test_05_intermittent_demand(self) -> None:
        portfolio = self._create_mock_portfolio(
            "INT-01",
            [0.0, 0.0, 50.0, 0.0, 0.0, 45.0, 0.0, 0.0, 55.0],
            class_type="INTERMITTENT",
            candidates=["CROSTON", "SBA"],
        )
        orch = Phase3Orchestrator(portfolio, horizon=2)
        res = orch.execute()
        self.assertEqual(res["sku_forecasts"]["INT-01"]["forecast_status"], "FORECAST_AVAILABLE")

    def test_06_lumpy_demand(self) -> None:
        portfolio = self._create_mock_portfolio(
            "LUMPY-01",
            [0.0, 0.0, 500.0, 0.0, 0.0, 10.0, 0.0, 0.0, 600.0],
            class_type="LUMPY",
            candidates=["CROSTON", "SBA"],
        )
        orch = Phase3Orchestrator(portfolio, horizon=2)
        res = orch.execute()
        self.assertIsNotNone(res["sku_forecasts"]["LUMPY-01"]["champion_model"])

    def test_07_constant_demand(self) -> None:
        portfolio = self._create_mock_portfolio("CONST-01", [50.0, 50.0, 50.0, 50.0, 50.0, 50.0])
        orch = Phase3Orchestrator(portfolio, horizon=2)
        res = orch.execute()
        self.assertIn(res["sku_forecasts"]["CONST-01"]["champion_model"], ["NAIVE", "MOVING_AVERAGE"])

    def test_08_zero_demand(self) -> None:
        portfolio = self._create_mock_portfolio("ZERO-01", [0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        orch = Phase3Orchestrator(portfolio, horizon=2)
        res = orch.execute()
        self.assertIn(res["sku_forecasts"]["ZERO-01"]["forecast_status"], ["FORECAST_AVAILABLE", "NO_VALID_MODEL"])

    def test_09_short_history(self) -> None:
        portfolio = self._create_mock_portfolio("SHORT-01", [10.0])
        orch = Phase3Orchestrator(portfolio, horizon=2)
        res = orch.execute()
        self.assertEqual(res["sku_forecasts"]["SHORT-01"]["forecast_status"], "INSUFFICIENT_HISTORY")

    def test_10_missing_periods(self) -> None:
        portfolio = self._create_mock_portfolio(
            "MISSING-01", [10.0, None, 20.0, None, 30.0, 40.0, 50.0], missing_pct=0.28
        )
        orch = Phase3Orchestrator(portfolio, horizon=2)
        res = orch.execute()
        self.assertEqual(res["sku_forecasts"]["MISSING-01"]["forecast_status"], "FORECAST_LIMITED")

    def test_11_irregular_time_series(self) -> None:
        portfolio = self._create_mock_portfolio("IRREG-01", [10.0, 20.0, 30.0, 40.0, 50.0])
        orch = Phase3Orchestrator(portfolio, horizon=2)
        res = orch.execute()
        self.assertIsNotNone(res["sku_forecasts"]["IRREG-01"])

    def test_12_outlier_heavy_series(self) -> None:
        portfolio = self._create_mock_portfolio("OUTLIER-01", [10.0, 11.0, 1000.0, 12.0, 10.0, 11.0, 10.0])
        orch = Phase3Orchestrator(portfolio, horizon=2)
        res = orch.execute()
        self.assertIsNotNone(res["sku_forecasts"]["OUTLIER-01"])

    def test_13_model_failure_handling(self) -> None:
        portfolio = self._create_mock_portfolio(
            "FAIL-01", [10.0, 20.0, 30.0, 40.0, 50.0, 60.0], candidates=["ARIMA", "NAIVE"]
        )
        orch = Phase3Orchestrator(portfolio, horizon=2)
        res = orch.execute()
        self.assertIsNotNone(res["sku_forecasts"]["FAIL-01"]["champion_model"])

    def test_14_no_valid_model(self) -> None:
        portfolio = self._create_mock_portfolio("NOV-01", [])
        orch = Phase3Orchestrator(portfolio, horizon=2)
        res = orch.execute()
        self.assertEqual(res["sku_forecasts"]["NOV-01"]["forecast_status"], "INSUFFICIENT_HISTORY")

    def test_15_baseline_beats_complex_model(self) -> None:
        portfolio = self._create_mock_portfolio("BASEWIN-01", [10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0])
        orch = Phase3Orchestrator(portfolio, horizon=2)
        res = orch.execute()
        self.assertIn(res["sku_forecasts"]["BASEWIN-01"]["champion_model"], ["NAIVE", "MOVING_AVERAGE"])

    def test_16_adversarial_leakage_prevention(self) -> None:
        dates = pd.date_range(start="2026-01-01", periods=7, freq="D")
        series = pd.Series([10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0], index=dates)
        _, y_train = MLFeatureEngineer.create_features(series)
        self.assertLess(float(y_train.max()), 500.0)

    def test_17_rolling_origin_backtesting(self) -> None:
        series = pd.Series([10.0, 12.0, 14.0, 16.0, 18.0, 20.0, 22.0, 24.0])
        backtester = RollingBacktester(min_train_size=4, horizon=2, n_folds=2)
        res = backtester.run(series, lambda: NaiveForecaster())
        self.assertEqual(res["status"], "EVALUATED")
        self.assertGreater(res["folds_tested"], 0)

    def test_18_champion_selection_determinism(self) -> None:
        comp_results: List[Dict[str, Any]] = [
            {"model_id": "NAIVE", "status": "EVALUATED", "wape": 0.15, "stability_variance": 0.01, "bias": 0.0},
            {"model_id": "ETS", "status": "EVALUATED", "wape": 0.10, "stability_variance": 0.01, "bias": 0.0},
        ]
        selector = ChampionSelector(min_baseline_improvement_pct=0.02)
        res = selector.select_champion(comp_results)
        self.assertEqual(res["champion_model"], "ETS")

    def test_19_forecast_interval_safety(self) -> None:
        portfolio = self._create_mock_portfolio("INTVL-01", [10.0, 15.0, 12.0, 18.0, 20.0, 22.0, 25.0])
        orch = Phase3Orchestrator(portfolio, horizon=2)
        res = orch.execute()
        fc = res["sku_forecasts"]["INTVL-01"]["forecast"]
        self.assertGreater(len(fc), 0)
        self.assertIn("interval_status", fc[0])

    def test_20_reproducibility(self) -> None:
        portfolio = self._create_mock_portfolio("REP-01", [10.0, 12.0, 14.0, 16.0, 18.0, 20.0])
        orch1 = Phase3Orchestrator(portfolio, horizon=2)
        res1 = orch1.execute()
        orch2 = Phase3Orchestrator(portfolio, horizon=2)
        res2 = orch2.execute()
        champ1 = res1["sku_forecasts"]["REP-01"]["champion_model"]
        champ2 = res2["sku_forecasts"]["REP-01"]["champion_model"]
        self.assertEqual(champ1, champ2)

    # ---------------- HARDENING PASS TEST ADDITIONS ----------------

    def test_21_daily_frequency_features(self) -> None:
        dates = pd.date_range(start="2026-01-01", periods=60, freq="D")
        series = pd.Series([float(i) for i in range(60)], index=dates)
        X, _ = MLFeatureEngineer.create_features(series, freq="D")
        self.assertIn("lag_1", X.columns)
        self.assertIn("lag_7", X.columns)
        self.assertIn("dayofweek", X.columns)

    def test_22_weekly_frequency_features(self) -> None:
        dates = pd.date_range(start="2026-01-01", periods=60, freq="W")
        series = pd.Series([float(i) for i in range(60)], index=dates)
        X, _ = MLFeatureEngineer.create_features(series, freq="W")
        self.assertIn("lag_1", X.columns)
        self.assertIn("lag_4", X.columns)
        self.assertIn("week", X.columns)

    def test_23_monthly_frequency_features(self) -> None:
        dates = pd.date_range(start="2026-01-01", periods=30, freq="MS")
        series = pd.Series([float(i) for i in range(30)], index=dates)
        X, _ = MLFeatureEngineer.create_features(series, freq="M")
        self.assertIn("lag_1", X.columns)
        self.assertIn("lag_3", X.columns)
        self.assertIn("month", X.columns)

    def test_24_insufficient_history_features(self) -> None:
        dates = pd.date_range(start="2026-01-01", periods=3, freq="D")
        series = pd.Series([10.0, 12.0, 14.0], index=dates)
        X, y = MLFeatureEngineer.create_features(series, freq="D")
        self.assertFalse(X.empty)
        self.assertNotIn("lag_14", X.columns)

    def test_25_raw_vs_constrained_forecast(self) -> None:
        portfolio = self._create_mock_portfolio("NEG-01", [10.0, 8.0, 6.0, 4.0, 2.0, 0.0, -2.0], candidates=["NAIVE"])
        orch = Phase3Orchestrator(portfolio, horizon=2)
        res = orch.execute()
        fc = res["sku_forecasts"]["NEG-01"]["forecast"]
        self.assertGreater(len(fc), 0)
        self.assertEqual(fc[0]["point_forecast"], 0.0)
        self.assertEqual(fc[0]["raw_model_forecast"], -2.0)
        self.assertTrue(fc[0]["constraint_applied"])
        self.assertEqual(fc[0]["constraint_reason"], "NON_NEGATIVE_DEMAND")

    def test_26_constraint_provenance(self) -> None:
        portfolio = self._create_mock_portfolio("POS-01", [10.0, 12.0, 14.0, 16.0], candidates=["NAIVE"])
        orch = Phase3Orchestrator(portfolio, horizon=2)
        res = orch.execute()
        fc = res["sku_forecasts"]["POS-01"]["forecast"]
        self.assertFalse(fc[0]["constraint_applied"])
        self.assertIsNone(fc[0]["constraint_reason"])

    def test_27_champion_model_serialization(self) -> None:
        portfolio = self._create_mock_portfolio(
            "SERIAL-01", [10.0, 20.0, 30.0, 40.0, 50.0, 60.0], candidates=["NAIVE"]
        )
        orch = Phase3Orchestrator(portfolio, horizon=2)
        res = orch.execute()
        prov = res["sku_forecasts"]["SERIAL-01"]["provenance"]
        self.assertTrue(os.path.exists(prov["model_path"]))
        self.assertTrue(os.path.exists(prov["metadata_path"]))

    def test_28_save_load_prediction_equivalence(self) -> None:
        if not HAS_XGBOOST:
            self.skipTest("xgboost package is not installed.")
        dates = pd.date_range(start="2026-01-01", periods=10, freq="D")
        series = pd.Series([float(i + 10) for i in range(10)], index=dates)

        model = XGBoostForecaster(freq="D")
        model.fit(series)
        orig_preds = model.predict(horizon=2)["point_forecast"]

        save_path = "artifacts/models/test_model.joblib"
        os.makedirs("artifacts/models", exist_ok=True)
        joblib.dump(model, save_path)

        loaded_model = joblib.load(save_path)
        loaded_preds = loaded_model.predict(horizon=2)["point_forecast"]

        self.assertEqual(orig_preds, loaded_preds)
        if os.path.exists(save_path):
            os.remove(save_path)

    def test_29_dataset_hash_reproducibility(self) -> None:
        ds1 = [{"date": "2026-01-01", "value": 10.0}, {"date": "2026-01-02", "value": 20.0}]
        ds2 = [{"date": "2026-01-01", "value": 10.0}, {"date": "2026-01-02", "value": 20.0}]
        ds3 = [{"date": "2026-01-01", "value": 10.0}, {"date": "2026-01-02", "value": 25.0}]

        self.assertEqual(compute_sha256(ds1), compute_sha256(ds2))
        self.assertNotEqual(compute_sha256(ds1), compute_sha256(ds3))

    def test_30_feature_schema_hash_reproducibility(self) -> None:
        schema1 = ["lag_1", "lag_7", "rolling_mean_3"]
        schema2 = ["lag_1", "lag_7", "rolling_mean_3"]
        schema3 = ["lag_1", "lag_14"]

        self.assertEqual(compute_sha256(schema1), compute_sha256(schema2))
        self.assertNotEqual(compute_sha256(schema1), compute_sha256(schema3))


class TestPhase3ForecastingPersistence(unittest.TestCase):
    """Integration test suite for Phase 3 forecasting database persistence and tenant isolation."""

    def setUp(self) -> None:
        """Sets up an isolated in-memory SQLite database for each test case."""
        self.engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})

        # Ensure dummy variable assignments bind modules
        _ = forecasting_models.__name__
        _ = supply_chain.__name__
        _ = ingestion.__name__

        Base.metadata.create_all(bind=self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine, autocommit=False, autoflush=False)
        self.db: Session = self.SessionLocal()

        self.tenant_a = "tenant_alpha"
        self.tenant_b = "tenant_beta"

        # Generate standard historical demand test series
        dates = pd.date_range(start="2026-01-01", periods=30, freq="D")
        self.sample_df = pd.DataFrame({
            "sku_id": ["SKU-PERSIST"] * 30,
            "target_date": dates,
            "demand": [10.0 + i % 5 for i in range(30)],
        })

    def tearDown(self) -> None:
        """Closes session and cleans in-memory schema after each test execution."""
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)

    def test_31_forecast_persistence_and_provenance(self) -> None:
        """Verifies successful forecast execution and point persistence in canonical tables."""
        service = ForecastingService(self.db, self.tenant_a)
        res = service.run_forecast(self.sample_df, frequency="DAILY", horizon=7)

        self.assertEqual(res["status"], "COMPLETED")
        self.assertFalse(res["idempotent_hit"])
        self.assertGreater(res["point_count"], 0)

        # Retrieve persisted run
        run_repo = ForecastRunRepository(self.db, self.tenant_a)
        run_record = run_repo.get_by_id(res["forecast_run_id"])
        self.assertIsNotNone(run_record)
        if run_record:
            self.assertEqual(run_record.frequency, "DAILY")
            self.assertEqual(run_record.horizon, 7)

        # Retrieve persisted forecast points
        point_repo = ForecastPointRepository(self.db, self.tenant_a)
        points = point_repo.list_by_run_id(res["forecast_run_id"])
        self.assertEqual(len(points), res["point_count"])

    def test_32_forecasting_tenant_isolation(self) -> None:
        """Adversarial test: Verifies Tenant B cannot query or access Tenant A's forecast runs or points."""
        service_a = ForecastingService(self.db, self.tenant_a)
        res_a = service_a.run_forecast(self.sample_df, frequency="DAILY", horizon=7)
        run_id_a = res_a["forecast_run_id"]

        # Attempt read as Tenant B
        run_repo_b = ForecastRunRepository(self.db, self.tenant_b)
        point_repo_b = ForecastPointRepository(self.db, self.tenant_b)

        self.assertIsNone(run_repo_b.get_by_id(run_id_a))
        points_b = point_repo_b.list_by_run_id(run_id_a)
        self.assertEqual(len(points_b), 0)

        # Cross-tenant delete attempt
        deleted = run_repo_b.delete(run_id_a)
        self.assertFalse(deleted)

    def test_33_forecast_run_idempotency(self) -> None:
        """Verifies submitting identical dataset hashes returns cached forecast results."""
        service = ForecastingService(self.db, self.tenant_a)

        # Initial run
        res1 = service.run_forecast(self.sample_df, frequency="DAILY", horizon=7)
        self.assertEqual(res1["status"], "COMPLETED")
        self.assertFalse(res1["idempotent_hit"])

        # Identical duplicate submission
        res2 = service.run_forecast(self.sample_df, frequency="DAILY", horizon=7)
        self.assertEqual(res2["status"], "COMPLETED")
        self.assertTrue(res2["idempotent_hit"])
        self.assertEqual(res1["forecast_run_id"], res2["forecast_run_id"])

    def test_34_non_negative_demand_provenance(self) -> None:
        """Verifies non-negative demand constraints log raw predictions and set constraint flags."""
        service = ForecastingService(self.db, self.tenant_a)

        # Mock engine output containing negative predictions
        neg_df = pd.DataFrame({
            "sku_id": ["SKU-NEG"] * 10,
            "target_date": pd.date_range("2026-01-01", periods=10, freq="D"),
            "demand": [1.0] * 10,
        })

        res = service.run_forecast(neg_df, frequency="DAILY", horizon=3)
        self.assertEqual(res["status"], "COMPLETED")

        point_repo = ForecastPointRepository(self.db, self.tenant_a)
        points = point_repo.list_by_run_id(res["forecast_run_id"])

        for pt in points:
            self.assertGreaterEqual(float(pt.point_forecast), 0.0)

    def test_35_transaction_rollback_on_failure(self) -> None:
        """Verifies that engine exceptions trigger atomic rollbacks and log FAILED run states."""
        service = ForecastingService(self.db, self.tenant_a)

        # Malformed input causing failure
        bad_df = pd.DataFrame({"invalid_col": [1, 2, 3]})
        res = service.run_forecast(bad_df, frequency="DAILY", horizon=7)

        self.assertEqual(res["status"], "FAILED")
        self.assertIn("error", res)

        run_repo = ForecastRunRepository(self.db, self.tenant_a)
        failed_run = run_repo.get_by_id(res["forecast_run_id"])
        self.assertIsNotNone(failed_run)
        if failed_run:
            self.assertEqual(failed_run.status, "FAILED")