"""Enterprise supply intelligence service bridging canonical persistence and analytical engines."""

import json
import uuid
import hashlib
from typing import Any, Dict, List, Optional, cast
import pandas as pd
from sqlalchemy.orm import Session

from aurix_core.config.settings import settings
from aurix_core.database.models.supply_intelligence import (
    SupplyIntelligenceRun,
    SupplierPerformance,
    ReplenishmentRecommendation,
)
from aurix_core.database.repositories.supply_intelligence import (
    SupplyIntelligenceRunRepository,
    SupplierPerformanceRepository,
    ReplenishmentRecommendationRepository,
)
import aurix_core.supply.orchestrator as supply_orch_module


class SupplyIntelligenceService:
    """
    Enterprise service adapter for Phase 5 Supply Intelligence.

    Orchestrates multi-tenant data retrieval, idempotency hashing, mathematical execution,
    and transaction-safe canonical persistence while preserving zero-fabrication.
    """

    def __init__(self, db: Session, tenant_id: Optional[str] = None) -> None:
        self.db = db
        self.tenant_id = tenant_id or settings.default_tenant_id
        self.run_repo = SupplyIntelligenceRunRepository(db, self.tenant_id)
        self.perf_repo = SupplierPerformanceRepository(db, self.tenant_id)
        self.rec_repo = ReplenishmentRecommendationRepository(db, self.tenant_id)

    def _compute_dataset_hash(self, payload: Dict[str, Any], config: Dict[str, Any]) -> str:
        """Computes deterministic SHA-256 hash across canonical inputs and configuration."""
        data_str = json.dumps({"payload": payload, "config": config}, sort_keys=True, default=str)
        return hashlib.sha256(data_str.encode("utf-8")).hexdigest()

    def _execute_supply_engine(
        self, payload: Dict[str, Any], config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Safely invokes the existing supply orchestrator without modifying mathematical core."""
        for attr in ["Phase5Orchestrator", "SupplyOrchestrator", "SupplyIntelligenceOrchestrator", "SupplyEngine"]:
            if hasattr(supply_orch_module, attr):
                cls = getattr(supply_orch_module, attr)
                inst = None
                try:
                    inst = cls(payload=payload, config=config)
                except TypeError:
                    try:
                        p4_out = payload.get("p4_output", payload)
                        sup_data = payload.get("supplier_data", payload.get("candidates", payload))
                        inst = cls(p4_out, supplier_data=sup_data, config=config)
                    except TypeError:
                        try:
                            inst = cls(payload)
                        except TypeError:
                            inst = cls()

                if inst is not None and hasattr(inst, "execute"):
                    res = inst.execute()
                    if isinstance(res, dict):
                        return cast(Dict[str, Any], res)

        # Fallback to direct function invocation
        if hasattr(supply_orch_module, "execute_supply"):
            res = getattr(supply_orch_module, "execute_supply")(payload, config)
            if isinstance(res, dict):
                return cast(Dict[str, Any], res)

        raise RuntimeError("Unable to resolve supply orchestrator execution entrypoint.")

    def run_supply_intelligence(
        self,
        input_payload: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None,
        force_recompute: bool = False,
    ) -> Dict[str, Any]:
        """Executes a supply intelligence run with idempotency checks and atomic database persistence."""
        exec_config = config or {}
        dataset_hash = self._compute_dataset_hash(input_payload, exec_config)

        # 1. Idempotency Check
        if not force_recompute:
            existing_run = self.run_repo.get_by_hash(dataset_hash)
            if existing_run:
                run_id_str = str(getattr(existing_run, "id"))
                existing_perfs = self.perf_repo.list_by_run_id(run_id_str)
                existing_recs = self.rec_repo.list_by_run_id(run_id_str)
                return {
                    "status": "COMPLETED",
                    "idempotent_hit": True,
                    "supply_run_id": run_id_str,
                    "dataset_hash": dataset_hash,
                    "performance_count": len(existing_perfs),
                    "recommendation_count": len(existing_recs),
                    "message": "Returned cached supply intelligence run for identical inputs.",
                }

        # 2. Generate Run ID & Record Initial State
        run_id = f"P5_RUN_{uuid.uuid4().hex[:12]}"
        run_record = SupplyIntelligenceRun(
            id=run_id,
            dataset_hash=dataset_hash,
            status="EXECUTING",
            configuration=json.dumps(exec_config),
            tenant_id=self.tenant_id,
        )
        self.run_repo.create(run_record)

        # 3. Execute Mathematical Engine
        try:
            engine_output = self._execute_supply_engine(input_payload, exec_config)

            def _safe_float(val: Any) -> Optional[float]:
                if val is None or pd.isna(val):
                    return None
                try:
                    return float(val)
                except (ValueError, TypeError):
                    return None

            def _safe_int(val: Any, default: int = 0) -> int:
                if val is None or pd.isna(val):
                    return default
                try:
                    return int(val)
                except (ValueError, TypeError):
                    return default

            # Persist Supplier Performance Records
            perfs_data = engine_output.get("supplier_performances", [])
            perf_records: List[SupplierPerformance] = []
            for p in perfs_data:
                drivers = p.get("risk_drivers")
                drivers_str: Optional[str] = None
                if isinstance(drivers, (list, dict)):
                    drivers_str = json.dumps(drivers)
                elif drivers is not None:
                    drivers_str = str(drivers)

                perf_rec = SupplierPerformance(
                    run_id=run_id,
                    supplier_id=str(p.get("supplier_id", "UNKNOWN_SUPPLIER")),
                    evaluated_order_count=_safe_int(p.get("evaluated_order_count"), default=0),
                    otd_rate=_safe_float(p.get("otd_rate")),
                    in_full_rate=_safe_float(p.get("in_full_rate")),
                    otif_rate=_safe_float(p.get("otif_rate")),
                    fill_rate=_safe_float(p.get("fill_rate")),
                    lead_time_mean=_safe_float(p.get("lead_time_mean")),
                    lead_time_std=_safe_float(p.get("lead_time_std")),
                    defect_rate=_safe_float(p.get("defect_rate")),
                    risk_score=_safe_float(p.get("risk_score")),
                    risk_level=p.get("risk_level", "UNASSESSED"),
                    risk_drivers=drivers_str,
                    tenant_id=self.tenant_id,
                )
                perf_records.append(perf_rec)

            for pref in perf_records:
                self.perf_repo.create(pref)

            # Persist Replenishment Recommendations
            recs_data = engine_output.get("replenishment_recommendations", [])
            rec_records: List[ReplenishmentRecommendation] = []
            for r in recs_data:
                pol_id = r.get("replenishment_policy_id")
                pol_id_int = int(pol_id) if pol_id is not None and str(pol_id).isdigit() else None

                rec_rec = ReplenishmentRecommendation(
                    run_id=run_id,
                    replenishment_policy_id=pol_id_int,
                    sku_id=str(r.get("sku_id", "UNKNOWN_SKU")),
                    supplier_id=str(r.get("supplier_id", "UNKNOWN_SUPPLIER")),
                    raw_quantity=float(r.get("raw_quantity", 0.0)),
                    constrained_quantity=float(r.get("constrained_quantity", 0.0)),
                    moq_applied=bool(r.get("moq_applied", False)),
                    pack_size_applied=bool(r.get("pack_size_applied", False)),
                    unit_price=_safe_float(r.get("unit_price")),
                    total_purchase_cost=_safe_float(r.get("total_purchase_cost")),
                    currency=r.get("currency"),
                    selection_rank=_safe_int(r.get("selection_rank"), default=1),
                    selection_reason=r.get("selection_reason"),
                    single_source_dependency=bool(r.get("single_source_dependency", False)),
                    value_state=str(r.get("value_state", "COMPUTED")),
                    tenant_id=self.tenant_id,
                )
                rec_records.append(rec_rec)

            for rrec in rec_records:
                self.rec_repo.create(rrec)

            # Update Run Status to Completed
            setattr(run_record, "status", "COMPLETED")
            setattr(run_record, "provenance", json.dumps(engine_output.get("provenance", {})))
            self.db.commit()

            return {
                "status": "COMPLETED",
                "idempotent_hit": False,
                "supply_run_id": run_id,
                "dataset_hash": dataset_hash,
                "performance_count": len(perf_records),
                "recommendation_count": len(rec_records),
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
                "supply_run_id": run_id,
                "dataset_hash": dataset_hash,
                "error": str(e),
            }