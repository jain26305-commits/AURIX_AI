"""Enterprise inventory intelligence service bridging canonical persistence and analytical engines."""

import json
import uuid
import hashlib
from typing import Any, Dict, List, Optional, cast
import pandas as pd
from sqlalchemy.orm import Session

from aurix_core.config.settings import settings
from aurix_core.database.models.inventory_intelligence import InventoryIntelligenceRun, ReplenishmentPolicy
from aurix_core.database.repositories.inventory_intelligence import (
    InventoryIntelligenceRunRepository,
    ReplenishmentPolicyRepository,
)
import aurix_core.inventory.orchestrator as inv_orch_module


class InventoryIntelligenceService:
    """
    Enterprise service adapter for Phase 4 Inventory Intelligence.

    Orchestrates multi-tenant data retrieval, idempotency hashing, mathematical execution,
    and transaction-safe canonical persistence while preserving zero-fabrication.
    """

    def __init__(self, db: Session, tenant_id: Optional[str] = None) -> None:
        self.db = db
        self.tenant_id = tenant_id or settings.default_tenant_id
        self.run_repo = InventoryIntelligenceRunRepository(db, self.tenant_id)
        self.policy_repo = ReplenishmentPolicyRepository(db, self.tenant_id)

    def _compute_dataset_hash(self, data: Dict[str, Any], config: Dict[str, Any]) -> str:
        """Computes deterministic SHA-256 hash across canonical inputs and configuration."""
        payload = json.dumps({"data": data, "config": config}, sort_keys=True, default=str)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def _execute_inventory_engine(self, portfolio_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Safely invokes the existing inventory orchestrator without modifying mathematical core."""
        for attr in ["InventoryOrchestrator", "Phase4Orchestrator", "InventoryEngine", "ReplenishmentOrchestrator"]:
            if hasattr(inv_orch_module, attr):
                cls = getattr(inv_orch_module, attr)
                inst = cls(portfolio_data=portfolio_data, config=config) if hasattr(cls, "__init__") else cls()
                if hasattr(inst, "execute"):
                    res = inst.execute()
                    if isinstance(res, dict):
                        return cast(Dict[str, Any], res)

        # Fallback to direct function invocation
        if hasattr(inv_orch_module, "execute_inventory"):
            res = getattr(inv_orch_module, "execute_inventory")(portfolio_data, config)
            if isinstance(res, dict):
                return cast(Dict[str, Any], res)

        raise RuntimeError("Unable to resolve inventory orchestrator execution entrypoint.")

    def run_inventory_intelligence(
        self,
        portfolio_input: Dict[str, Any],
        forecast_run_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        force_recompute: bool = False,
    ) -> Dict[str, Any]:
        """
        Executes an inventory intelligence run with idempotency checks and atomic database persistence.
        """
        exec_config = config or {}
        dataset_hash = self._compute_dataset_hash(portfolio_input, exec_config)

        # 1. Idempotency Check
        if not force_recompute:
            existing_run = self.run_repo.get_by_hash(dataset_hash)
            if existing_run:
                existing_policies = self.policy_repo.list_by_run_id(str(getattr(existing_run, "id")))
                return {
                    "status": "COMPLETED",
                    "idempotent_hit": True,
                    "inventory_run_id": str(getattr(existing_run, "id")),
                    "dataset_hash": dataset_hash,
                    "policy_count": len(existing_policies),
                    "message": "Returned cached inventory intelligence run for identical inputs.",
                }

        # 2. Generate Run ID & Record Initial State
        run_id = f"P4_RUN_{uuid.uuid4().hex[:12]}"
        run_record = InventoryIntelligenceRun(
            id=run_id,
            forecast_run_id=forecast_run_id,
            dataset_hash=dataset_hash,
            status="EXECUTING",
            configuration=json.dumps(exec_config),
            tenant_id=self.tenant_id,
        )
        self.run_repo.create(run_record)

        # 3. Execute Mathematical Engine
        try:
            engine_output = self._execute_inventory_engine(portfolio_input, exec_config)
            policy_records: List[ReplenishmentPolicy] = []

            policies_data = engine_output.get("replenishment_policies", [])

            # 4. Extract Policies, Enforce Zero-Fabrication & Provenance
            def _safe_float(val: Any) -> Optional[float]:
                if val is None or pd.isna(val):
                    return None
                try:
                    return float(val)
                except (ValueError, TypeError):
                    return None

            for p in policies_data:
                policy_record = ReplenishmentPolicy(
                    run_id=run_id,
                    sku_id=str(p.get("sku_id", "UNKNOWN_SKU")),
                    location_id=p.get("location_id"),
                    expected_daily_demand=_safe_float(p.get("expected_daily_demand")),
                    lead_time_days=_safe_float(p.get("lead_time_days")),
                    safety_stock=_safe_float(p.get("safety_stock")),
                    reorder_point=_safe_float(p.get("reorder_point")),
                    eoq=_safe_float(p.get("eoq")),
                    reorder_triggered=bool(p.get("reorder_triggered", False)),
                    reorder_reason=p.get("reorder_reason"),
                    raw_order_quantity=_safe_float(p.get("raw_order_quantity")),
                    constrained_order_quantity=_safe_float(p.get("constrained_order_quantity")),
                    constraint_applied=bool(p.get("constraint_applied", False)),
                    constraint_reason=p.get("constraint_reason"),
                    risk_status=p.get("risk_status", "UNKNOWN"),
                    holding_cost_exposure=_safe_float(p.get("holding_cost_exposure")),
                    value_state=str(p.get("value_state", "COMPUTED")),
                    tenant_id=self.tenant_id,
                )
                policy_records.append(policy_record)

            # Bulk persist computed policies
            for pol_rec in policy_records:
                self.policy_repo.create(pol_rec)

            # Update Run Status to Completed
            setattr(run_record, "status", "COMPLETED")
            setattr(run_record, "provenance", json.dumps(engine_output.get("provenance", {})))
            self.db.commit()

            return {
                "status": "COMPLETED",
                "idempotent_hit": False,
                "inventory_run_id": run_id,
                "dataset_hash": dataset_hash,
                "policy_count": len(policy_records),
                "engine_output": engine_output,
            }

        except Exception as e:
            self.db.rollback()
            setattr(run_record, "status", "FAILED")
            setattr(run_record, "provenance", json.dumps({"error": str(e)}))
            self.db.add(run_record)
            self.db.flush()
            self.db.commit()
            return {
                "status": "FAILED",
                "inventory_run_id": run_id,
                "dataset_hash": dataset_hash,
                "error": str(e),
            }
