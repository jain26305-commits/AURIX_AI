"""Multi-source data reconciliation and conflict resolution engine for Phase 12."""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from aurix_core.config.settings import settings
from aurix_core.integrations.contracts import ReconciliationRecord, ReconciliationStatus

# Default configurable source priority by business domain
DEFAULT_DOMAIN_SOURCE_PRIORITY: Dict[str, List[str]] = {
    "inventory": ["WMS", "ERP", "POS", "SFTP", "API"],
    "finance": ["ERP", "CRM", "ECOMMERCE", "API"],
    "shipments": ["TMS", "TELEMATICS", "CARRIER", "ERP", "API"],
    "orders": ["ECOMMERCE", "CRM", "ERP", "POS", "API"],
    "suppliers": ["ERP", "SUPPLIER_PORTAL", "EDI", "API"],
}


class ReconciliationEngine:
    """Detects, classifies, and reconciles variances across multi-source enterprise systems."""

    @staticmethod
    def compare_numeric_values(
        val_a: float,
        val_b: float,
        material_threshold_pct: Optional[float] = None,
    ) -> Tuple[float, float, ReconciliationStatus]:
        """
        Compares two numeric values and determines variance materiality.
        Returns: (absolute_difference, variance_pct, reconciliation_status)
        """
        threshold = (
            material_threshold_pct
            if material_threshold_pct is not None
            else settings.reconciliation_material_variance_pct
        )

        abs_diff = round(abs(val_a - val_b), 4)

        if val_a == 0.0 and val_b == 0.0:
            return 0.0, 0.0, ReconciliationStatus.MATCHED

        # Baseline comparison using max magnitude to prevent extreme skew
        baseline = max(abs(val_a), abs(val_b))
        variance_pct = round((abs_diff / baseline) * 100.0, 2) if baseline > 0 else 0.0

        if abs_diff == 0.0:
            status = ReconciliationStatus.MATCHED
        elif variance_pct <= threshold:
            status = ReconciliationStatus.MINOR_VARIANCE
        else:
            status = ReconciliationStatus.MATERIAL_VARIANCE

        return abs_diff, variance_pct, status

    @classmethod
    def get_preferred_source(
        cls,
        entity_type: str,
        available_sources: List[str],
        custom_priorities: Optional[Dict[str, List[str]]] = None,
    ) -> str:
        """Determines the authoritative source based on domain hierarchy rules."""
        priorities = (custom_priorities or {}).get(
            entity_type.lower(),
            DEFAULT_DOMAIN_SOURCE_PRIORITY.get(entity_type.lower(), []),
        )

        for preferred in priorities:
            for actual in available_sources:
                if preferred.upper() in actual.upper():
                    return actual

        return available_sources[0] if available_sources else "UNKNOWN"

    @classmethod
    def reconcile_entity(
        cls,
        tenant_id: str,
        entity_type: str,
        entity_key: str,
        source_a: str,
        value_a: float,
        source_b: str,
        value_b: float,
        material_threshold_pct: Optional[float] = None,
        custom_priorities: Optional[Dict[str, List[str]]] = None,
    ) -> ReconciliationRecord:
        """
        Reconciles metric values between two sources for a specific business entity.
        """
        abs_diff, var_pct, status = cls.compare_numeric_values(
            val_a=value_a,
            val_b=value_b,
            material_threshold_pct=material_threshold_pct,
        )

        preferred = cls.get_preferred_source(
            entity_type=entity_type,
            available_sources=[source_a, source_b],
            custom_priorities=custom_priorities,
        )

        chosen_val = value_a if preferred == source_a else value_b
        resolution_msg = (
            f"Resolved to {preferred} ({chosen_val}) based on domain priority hierarchy."
            if status != ReconciliationStatus.MATCHED
            else "Values identical across authoritative sources."
        )

        return ReconciliationRecord(
            reconciliation_id=f"REC-{uuid.uuid4().hex[:10].upper()}",
            tenant_id=tenant_id,
            entity_type=entity_type,
            entity_key=entity_key,
            primary_source=source_a,
            primary_value=value_a,
            secondary_source=source_b,
            secondary_value=value_b,
            absolute_difference=abs_diff,
            variance_pct=var_pct,
            reconciliation_status=status,
            resolution_applied=resolution_msg,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

    @classmethod
    def reconcile_datasets(
        cls,
        tenant_id: str,
        entity_type: str,
        dataset_a: List[Dict[str, Any]],
        source_a: str,
        dataset_b: List[Dict[str, Any]],
        source_b: str,
        key_field: str,
        metric_field: str,
        material_threshold_pct: Optional[float] = None,
    ) -> Tuple[List[Dict[str, Any]], List[ReconciliationRecord]]:
        """
        Performs batch reconciliation across two source datasets.
        Returns: (reconciled_canonical_records, reconciliation_audit_trail)
        """
        # Index datasets by key
        map_a: Dict[str, Dict[str, Any]] = {}
        for r in dataset_a:
            k = str(r.get(key_field, "")).strip()
            if k:
                map_a[k] = r

        map_b: Dict[str, Dict[str, Any]] = {}
        for r in dataset_b:
            k = str(r.get(key_field, "")).strip()
            if k:
                map_b[k] = r

        all_keys = set(map_a.keys()).union(set(map_b.keys()))
        reconciled_records: List[Dict[str, Any]] = []
        audit_trail: List[ReconciliationRecord] = []

        preferred_source = cls.get_preferred_source(entity_type, [source_a, source_b])

        for key in sorted(list(all_keys)):
            row_a = map_a.get(key)
            row_b = map_b.get(key)

            if row_a and row_b:
                val_a = float(str(row_a.get(metric_field, 0.0)).replace(",", "").replace("$", ""))
                val_b = float(str(row_b.get(metric_field, 0.0)).replace(",", "").replace("$", ""))

                rec_record = cls.reconcile_entity(
                    tenant_id=tenant_id,
                    entity_type=entity_type,
                    entity_key=key,
                    source_a=source_a,
                    value_a=val_a,
                    source_b=source_b,
                    value_b=val_b,
                    material_threshold_pct=material_threshold_pct,
                )
                audit_trail.append(rec_record)

                # Base chosen row on preferred source
                chosen_row = dict(row_a if preferred_source == source_a else row_b)
                chosen_row["_reconciliation_status"] = rec_record.reconciliation_status.value
                chosen_row["_variance_pct"] = rec_record.variance_pct
                reconciled_records.append(chosen_row)

            elif row_a:
                val_a = float(str(row_a.get(metric_field, 0.0)).replace(",", "").replace("$", ""))
                rec_record = ReconciliationRecord(
                    reconciliation_id=f"REC-{uuid.uuid4().hex[:10].upper()}",
                    tenant_id=tenant_id,
                    entity_type=entity_type,
                    entity_key=key,
                    primary_source=source_a,
                    primary_value=val_a,
                    secondary_source=source_b,
                    secondary_value=0.0,
                    absolute_difference=val_a,
                    variance_pct=100.0,
                    reconciliation_status=ReconciliationStatus.UNRESOLVED,
                    resolution_applied=f"Only present in {source_a}.",
                    created_at=datetime.now(timezone.utc).isoformat(),
                )
                audit_trail.append(rec_record)
                row_copy = dict(row_a)
                row_copy["_reconciliation_status"] = ReconciliationStatus.UNRESOLVED.value
                reconciled_records.append(row_copy)

            elif row_b:
                val_b = float(str(row_b.get(metric_field, 0.0)).replace(",", "").replace("$", ""))
                rec_record = ReconciliationRecord(
                    reconciliation_id=f"REC-{uuid.uuid4().hex[:10].upper()}",
                    tenant_id=tenant_id,
                    entity_type=entity_type,
                    entity_key=key,
                    primary_source=source_a,
                    primary_value=0.0,
                    secondary_source=source_b,
                    secondary_value=val_b,
                    absolute_difference=val_b,
                    variance_pct=100.0,
                    reconciliation_status=ReconciliationStatus.UNRESOLVED,
                    resolution_applied=f"Only present in {source_b}.",
                    created_at=datetime.now(timezone.utc).isoformat(),
                )
                audit_trail.append(rec_record)
                row_copy = dict(row_b)
                row_copy["_reconciliation_status"] = ReconciliationStatus.UNRESOLVED.value
                reconciled_records.append(row_copy)

        return reconciled_records, audit_trail