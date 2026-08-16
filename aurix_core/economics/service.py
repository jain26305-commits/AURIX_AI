"""Enterprise transactional service adapter for Phase 8 Financial Intelligence and Scenario Simulation."""

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from aurix_core.database.models.economics import (
    FinancialBaselineSnapshot,
    FinancialIntelligenceRun,
    ScenarioMetricSnapshot,
    ScenarioRun,
)
from aurix_core.database.repositories.economics import (
    FinancialBaselineSnapshotRepository,
    FinancialIntelligenceRunRepository,
    ScenarioMetricSnapshotRepository,
    ScenarioRunRepository,  # noqa: F401
)
from aurix_core.economics.orchestrator import Phase8Orchestrator


class FinancialIntelligenceService:
    """Manages transactional execution, persistence, idempotency, and tenant isolation for Financial Intelligence."""

    def __init__(self, db: Session, tenant_id: str) -> None:
        self.db = db
        self.tenant_id = tenant_id
        self.run_repo = FinancialIntelligenceRunRepository(db, tenant_id)
        self.baseline_repo = FinancialBaselineSnapshotRepository(db, tenant_id)
        self.scenario_run_repo = ScenarioRunRepository(db, tenant_id)
        self.scenario_metric_repo = ScenarioMetricSnapshotRepository(db, tenant_id)

    def _compute_dataset_hash(self, payload: Dict[str, Any], config: Dict[str, Any]) -> str:
        """Computes a deterministic SHA-256 hash of the input payload and configuration."""
        canonical_str = json.dumps(
            {"payload": payload, "config": config}, sort_keys=True, default=str
        )
        return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()

    def run_financial_intelligence(
        self,
        payload: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Executes the financial intelligence and scenario simulation pipeline with idempotency caching,
        multi-tenant security enforcement, and atomic transaction commit/rollback safety.
        """
        cfg_dict = config.get("config", config) if config else {}
        if not isinstance(cfg_dict, dict):
            cfg_dict = {}

        dataset_hash = self._compute_dataset_hash(payload, cfg_dict)

        # 1. Check Idempotency Cache
        existing_run = self.run_repo.get_by_hash(dataset_hash)
        if existing_run and getattr(existing_run, "status", None) == "COMPLETED":
            return {
                "status": "COMPLETED",
                "idempotent_hit": True,
                "financial_run_id": getattr(existing_run, "id"),
                "dataset_hash": dataset_hash,
                "provenance": json.loads(getattr(existing_run, "provenance", "{}") or "{}"),
            }

        # 2. Initialize Execution Run Record
        run_id = f"RUN-FIN-{uuid.uuid4().hex[:12].upper()}"

        run_rec = FinancialIntelligenceRun(
            id=run_id,
            tenant_id=self.tenant_id,
            dataset_hash=dataset_hash,
            status="EXECUTING",
            configuration=json.dumps(cfg_dict, default=str),
            provenance=json.dumps({"started_at": datetime.now(timezone.utc).isoformat()}, default=str),
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(run_rec)
        self.db.flush()

        # 3. Execute Phase 8 Financial Orchestrator
        orchestrator = Phase8Orchestrator(
            phase7b_decision_output=payload,
        )
        contract = orchestrator.execute()
        contract_dict = contract if isinstance(contract, dict) else dict(contract)

        # 4. Persist Financial Baseline Snapshot
        baseline_data = contract_dict.get("portfolio_financials_by_currency", {})
        baseline_id = f"BASE-{uuid.uuid4().hex[:10].upper()}"
        baseline_rec = FinancialBaselineSnapshot(
            id=baseline_id,
            tenant_id=self.tenant_id,
            run_id=run_id,
            currency="USD",
            baseline_metrics_json=json.dumps(baseline_data, default=str),
            value_state="DERIVED",
        )
        self.db.add(baseline_rec)

        # 5. Persist Scenarios & Scenario Metrics
        scenarios_map = contract_dict.get("scenarios", {})
        scenario_count = 0
        for scn_id, scn_data in scenarios_map.items():
            scn_run_id = f"SCRUN-{uuid.uuid4().hex[:10].upper()}"

            scn_run_rec = ScenarioRun(
                id=scn_run_id,
                tenant_id=self.tenant_id,
                run_id=run_id,
                scenario_id=str(scn_id),
                scenario_type=str(scn_data.get("scenario_type", "GENERIC")),
                scenario_description=str(scn_data.get("description", "")),
                parameters_json=json.dumps(scn_data, default=str),
                status=str(scn_data.get("status", "COMPUTED")),
            )
            self.db.add(scn_run_rec)

            scn_metric_rec = ScenarioMetricSnapshot(
                id=f"SCMET-{uuid.uuid4().hex[:10].upper()}",
                tenant_id=self.tenant_id,
                scenario_run_id=scn_run_id,
                currency="USD",
                scenario_metrics_json=json.dumps(
                    scn_data.get("financial_comparison_by_currency", {}), default=str
                ),
                deltas_json=json.dumps(scn_data.get("limitations", []), default=str),
                gate_status="RECOMMENDED",
            )
            self.db.add(scn_metric_rec)
            scenario_count += 1

        # 6. Update Run Record Status to COMPLETED
        provenance_meta = {
            "run_id": run_id,
            "scenario_count": scenario_count,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        run_rec.status = "COMPLETED"  # type: ignore[assignment]
        run_rec.provenance = json.dumps(provenance_meta, default=str)  # type: ignore[assignment]

        self.db.commit()

        return {
            "status": "COMPLETED",
            "idempotent_hit": False,
            "financial_run_id": run_id,
            "dataset_hash": dataset_hash,
            "scenario_count": scenario_count,
            "contract": contract_dict,
        }