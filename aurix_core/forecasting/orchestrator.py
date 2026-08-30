import os
import json
import uuid
import datetime
import io
import joblib  # type: ignore
import pandas as pd
from typing import Dict, Any, cast
from aurix_core.schema.phase3_contract import Phase3InputContract
from aurix_core.schema.phase4_contract import Phase4InputContract, ModelEvaluation
from aurix_core.forecasting.registry import ForecastStatus
from aurix_core.forecasting.gate import ModelEligibilityGate
from aurix_core.forecasting.competition import ModelCompetitionEngine
from aurix_core.forecasting.champion import ChampionSelector
from aurix_core.forecasting.generator import FinalForecastGenerator
from aurix_core.utils.provenance import compute_sha256
from aurix_core.mlops.artifact_storage import ArtifactStorage
from aurix_core.config.settings import settings


class Phase3Orchestrator:
    """Master controller for Phase 3 Forecasting, Model Competition, and Champion Selection."""

    def __init__(
        self,
        phase2_portfolio_output: Dict[str, Any],
        horizon: int = 2,
        artifacts_dir: str = "artifacts/models",
        tenant_id: str | None = None,
    ) -> None:
        self.phase2_data = phase2_portfolio_output
        self.horizon = horizon
        self.artifacts_dir = artifacts_dir
        self.tenant_id = tenant_id
        self.run_id = str(uuid.uuid4())
        self.timestamp = datetime.datetime.now().isoformat()
        os.makedirs(self.artifacts_dir, exist_ok=True)

    def execute(self) -> Dict[str, Any]:
        sku_intelligence = self.phase2_data.get("sku_intelligence", {})
        provenance_meta = self.phase2_data.get("provenance", {})

        sku_forecast_contracts: Dict[str, Dict[str, Any]] = {}
        portfolio_summary_stats: Dict[str, Any] = {
            "total_skus": len(sku_intelligence),
            "forecast_available": 0,
            "forecast_limited": 0,
            "no_valid_model": 0,
            "insufficient_history": 0,
            "champion_distribution": {},
            "average_wape": 0.0,
            "average_bias": 0.0,
            "baseline_win_rate": 0.0,
        }

        total_wape_accum = 0.0
        total_bias_accum = 0.0
        evaluated_count = 0
        baseline_wins = 0

        eligibility_gate = ModelEligibilityGate()
        competition_engine = ModelCompetitionEngine(horizon=self.horizon, n_folds=1, min_train_size=3)
        champion_selector = ChampionSelector(min_baseline_improvement_pct=0.02)
        forecast_generator = FinalForecastGenerator(horizon=self.horizon)

        for sku, contract_dict in sku_intelligence.items():
            contract = Phase3InputContract(**contract_dict)

            obs_list = contract.observed_data
            dates = [pd.to_datetime(item.date) for item in obs_list]
            values = [item.value if item.value is not None else float("nan") for item in obs_list]
            series = pd.Series(values, index=pd.DatetimeIndex(dates)).sort_index()

            # Cryptographic SHA-256 Dataset Hashing
            dataset_records = [{"date": item.date, "value": item.value} for item in obs_list]
            dataset_hash = compute_sha256(dataset_records)

            freq = contract.data_quality.get("frequency", "D")
            missing_pct = contract.missing_period_percentage
            demand_class = contract.inferred_classification.get("classification", "SMOOTH")
            seasonal_detected = contract.inferred_classification.get("seasonality", {}).get("detected", False)
            candidates = contract.model_candidates

            eligibility_report = eligibility_gate.evaluate_eligibility(
                candidates=candidates,
                series=series,
                freq=freq,
                missing_pct=missing_pct,
                demand_class=demand_class,
                seasonal_detected=seasonal_detected,
            )

            any_eligible = any(rep["eligible"] for rep in eligibility_report.values())

            if len(series.dropna()) < 2 or not any_eligible:
                status = (
                    ForecastStatus.INSUFFICIENT_HISTORY if len(series.dropna()) < 2 else ForecastStatus.NO_VALID_MODEL
                )
                key = "no_valid_model" if status == ForecastStatus.NO_VALID_MODEL else "insufficient_history"
                portfolio_summary_stats[key] = int(portfolio_summary_stats[key]) + 1

                phase4_contract = Phase4InputContract(
                    entity_id=sku,
                    forecast_status=status,
                    champion_model=None,
                    forecast_horizon=self.horizon,
                    forecast=[],
                    selection_reason="No eligible models or insufficient history available.",
                    baseline_model=None,
                    model_competition=[],
                    data_quality_flags=list(contract.data_quality.keys()),
                    limitations=contract.limitations + ["INSUFFICIENT_ELIGIBLE_MODELS"],
                    provenance={
                        "phase3_run_id": self.run_id,
                        "phase2_run_id": provenance_meta.get("phase1_run_id", "UNKNOWN"),
                        "dataset_hash": dataset_hash,
                        "feature_schema_hash": compute_sha256(["target_series"]),
                        "phase2_version": "2.0.0",
                        "phase3_version": "3.1.0",
                        "model_version": "3.1.0",
                        "engine_version": "3.1.0",
                    },
                )
                sku_forecast_contracts[sku] = phase4_contract.model_dump()
                continue

            competition_results = competition_engine.compete(series, eligibility_report, freq)
            model_eval_list = [ModelEvaluation(**m) for m in competition_results]
            selection_res = champion_selector.select_champion(competition_results)

            champion_model_id = selection_res["champion_model"]
            champion_eval = selection_res["champion_evaluation"]
            selection_reason = selection_res["selection_reason"]

            if not champion_model_id or not champion_eval:
                status = ForecastStatus.NO_VALID_MODEL
                portfolio_summary_stats["no_valid_model"] = int(portfolio_summary_stats["no_valid_model"]) + 1

                phase4_contract = Phase4InputContract(
                    entity_id=sku,
                    forecast_status=status,
                    champion_model=None,
                    forecast_horizon=self.horizon,
                    forecast=[],
                    selection_reason=selection_reason,
                    baseline_model=None,
                    model_competition=model_eval_list,
                    data_quality_flags=list(contract.data_quality.keys()),
                    limitations=contract.limitations + ["CHAMPION_SELECTION_FAILED"],
                    provenance={
                        "phase3_run_id": self.run_id,
                        "phase2_run_id": provenance_meta.get("phase1_run_id", "UNKNOWN"),
                        "dataset_hash": dataset_hash,
                        "feature_schema_hash": compute_sha256(["target_series"]),
                        "phase2_version": "2.0.0",
                        "phase3_version": "3.1.0",
                        "model_version": "3.1.0",
                        "engine_version": "3.1.0",
                    },
                )
                sku_forecast_contracts[sku] = phase4_contract.model_dump()
                continue

            baseline_ids = {"NAIVE", "MOVING_AVERAGE", "SEASONAL_NAIVE"}
            baselines_eval = [
                m for m in competition_results if m["model_id"] in baseline_ids and m.get("wape") is not None
            ]
            best_baseline_id = (
                min(baselines_eval, key=lambda x: float(x["wape"]))["model_id"] if baselines_eval else "NAIVE"
            )

            if champion_model_id in baseline_ids:
                baseline_wins += 1

            wape_val = champion_eval.get("wape")
            bias_val = champion_eval.get("bias")
            if wape_val is not None:
                total_wape_accum += float(wape_val)
            if bias_val is not None:
                total_bias_accum += float(bias_val)
            evaluated_count += 1

            champ_dist = cast(Dict[str, int], portfolio_summary_stats["champion_distribution"])
            champ_dist[champion_model_id] = champ_dist.get(champion_model_id, 0) + 1

            forecast_points, champion_obj, feature_schema = forecast_generator.generate(series, champion_model_id, freq)
            feature_schema_hash = compute_sha256(feature_schema)

            status = ForecastStatus.LIMITED if missing_pct > 0.10 else ForecastStatus.AVAILABLE
            key = "forecast_available" if status == ForecastStatus.AVAILABLE else "forecast_limited"
            portfolio_summary_stats[key] = int(portfolio_summary_stats[key]) + 1

            # Artifact storage is local for development/tests and durable Supabase Storage in production.
            sku_artifact_dir = os.path.join(self.artifacts_dir, sku)
            os.makedirs(sku_artifact_dir, exist_ok=True)

            model_path = os.path.join(sku_artifact_dir, "champion.joblib")
            metadata_path = os.path.join(sku_artifact_dir, "metadata.json")

            # Binary Champion Model Serialization
            model_reference = None
            tenant_id = str(
                self.tenant_id
                or provenance_meta.get("tenant_id")
                or settings.default_tenant_id
            )
            if champion_obj is not None:
                if settings.artifact_storage_backend == "local":
                    joblib.dump(champion_obj, model_path)
                    model_reference = model_path
                else:
                    model_buffer = io.BytesIO()
                    joblib.dump(champion_obj, model_buffer)
                    model_reference = ArtifactStorage.save_bytes(
                        tenant_id=tenant_id,
                        model_type="DEMAND_FORECAST",
                        version="3.1.0",
                        filename=f"{sku}__champion.joblib",
                        data=model_buffer.getvalue(),
                    )

                    # Keep a local filesystem copy for synchronous consumers
                    # and compatibility tests. Supabase remains the durable
                    # source of truth through model_reference.
                    model_bytes = model_buffer.getvalue()

                    with open(model_path, "wb") as model_file:
                        model_file.write(model_bytes)
                model_params = champion_obj.get_params()
            else:
                model_params = {}

            artifact_metadata = {
                "SKU": sku,
                "champion_model": champion_model_id,
                "engine_version": "3.1.0",
                "training_timestamp": self.timestamp,
                "forecast_horizon": self.horizon,
                "backtest_summary": champion_eval,
                "selection_reason": selection_reason,
                "dataset_hash": dataset_hash,
                "feature_schema": feature_schema,
                "feature_schema_hash": feature_schema_hash,
                "phase2_version": "2.0.0",
                "phase3_version": "3.1.0",
                "model_version": "3.1.0",
                "model_parameters": model_params,
            }

            metadata_bytes = json.dumps(artifact_metadata, indent=2).encode("utf-8")
            if settings.artifact_storage_backend == "local":
                with open(metadata_path, "wb") as f:
                    f.write(metadata_bytes)
                metadata_reference = metadata_path
            else:
                metadata_reference = ArtifactStorage.save_bytes(
                    tenant_id=tenant_id,
                    model_type="DEMAND_FORECAST",
                    version="3.1.0",
                    filename=f"{sku}__metadata.json",
                    data=metadata_bytes,
                    content_type="application/json",
                )

                # Keep a local metadata materialization for synchronous consumers
                # and compatibility with callers that expect provenance["metadata_path"]
                # to be a real filesystem path. Supabase remains the durable source
                # of truth through metadata_reference.
                with open(metadata_path, "wb") as metadata_file:
                    metadata_file.write(metadata_bytes)


            phase4_contract = Phase4InputContract(
                entity_id=sku,
                forecast_status=status,
                champion_model=champion_model_id,
                forecast_horizon=self.horizon,
                forecast=forecast_points,
                selection_reason=selection_reason,
                baseline_model=best_baseline_id,
                model_competition=model_eval_list,
                data_quality_flags=list(contract.data_quality.keys()),
                limitations=contract.limitations,
                provenance={
                    "phase3_run_id": self.run_id,
                    "phase2_run_id": provenance_meta.get("phase1_run_id", "UNKNOWN"),
                    "dataset_hash": dataset_hash,
                    "feature_schema_hash": feature_schema_hash,
                    "phase2_version": "2.0.0",
                    "phase3_version": "3.1.0",
                    "model_version": "3.1.0",
                    "engine_version": "3.1.0",
                    "artifact_dir": sku_artifact_dir if settings.artifact_storage_backend == "local" else None,
                    "model_path": model_path,
                    "metadata_path": metadata_path,
                    "model_storage_reference": model_reference,
                    "metadata_storage_reference": metadata_reference,
                },
            )
            sku_forecast_contracts[sku] = phase4_contract.model_dump()

        if evaluated_count > 0:
            portfolio_summary_stats["average_wape"] = round(total_wape_accum / evaluated_count, 4)
            portfolio_summary_stats["average_bias"] = round(total_bias_accum / evaluated_count, 4)
            portfolio_summary_stats["baseline_win_rate"] = round(baseline_wins / evaluated_count, 4)

        return {
            "run_id": self.run_id,
            "timestamp": self.timestamp,
            "portfolio_summary": portfolio_summary_stats,
            "sku_forecasts": sku_forecast_contracts,
            "phase4_contract_status": "READY",
        }
