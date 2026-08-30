"""Master customer data onboarding orchestration service for Phase 11."""

import hashlib
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

from sqlalchemy import text as sqlalchemy_text
from sqlalchemy.orm import Session
import pandas as pd

from aurix_core.database.models.ingestion import (
    IngestionRun,
    OnboardingDataset,
    OnboardingQuarantineRecord,
)
from aurix_core.data_foundation.db_mapper import CanonicalMapper
from aurix_core.intelligence.discovery import CapabilityDiscoveryEngine
from aurix_core.intelligence.incremental import (
    IncrementalMergeEngine,
    MergeResult,
)
from aurix_core.intelligence.readiness import DataReadinessEngine
from aurix_core.onboarding.contracts import (
    CapabilityOnboardingSummary,
    DuplicateCorrectionStatus,
    ManualMappingResolutionRequest,
    OnboardingResult,
    OnboardingStatus,
    SourceType,
)
from aurix_core.onboarding.parsers import DataParser
from aurix_core.onboarding.normalization import EnterpriseNormalizationEngine
from aurix_core.onboarding.quality_validator import (
    OnboardingQualityEngine,
)
from aurix_core.onboarding.safety import (
    FileSafetyException,
    FileSafetyValidator,
)
from aurix_core.onboarding.schema_discovery import (
    SchemaDiscoveryEngine,
)
from aurix_core.onboarding.semantic_mapper import SemanticMapper

logger = logging.getLogger(
    "aurix_core.onboarding.service"
)


class OnboardingService:
    """Coordinates autonomous customer data onboarding,
    schema discovery, mapping, and selective DAG execution.
    """

    @staticmethod
    def _bind_tenant_to_session(
        db: Session,
        tenant_id: str,
    ) -> None:
        """Bind the explicit onboarding tenant to the current PostgreSQL transaction."""
        clean_tenant_id = str(tenant_id).strip()

        if not clean_tenant_id:
            raise ValueError("tenant_id cannot be empty")

        db.execute(
            sqlalchemy_text(
                "SELECT set_config('app.tenant_id', :tenant_id, true)"
            ),
            {"tenant_id": clean_tenant_id},
        )

    @staticmethod
    def _compute_input_hash(content: bytes) -> str:
        """Computes deterministic SHA-256 digest of incoming raw content."""
        return hashlib.sha256(content).hexdigest()

    @staticmethod
    def _stage_dataset(
        db: Session,
        tenant_id: str,
        run_id: str,
        source_name: str,
        source_type: SourceType,
        input_hash: str,
        records: List[Dict[str, Any]],
        source_columns: Optional[List[str]],
        detected_entity: Optional[str],
        status: str,
    ) -> OnboardingDataset:
        """
        Persist the parsed source dataset so onboarding can be resumed
        without requiring the browser to resend the original records.
        """
        OnboardingService._bind_tenant_to_session(db, tenant_id)
        staged = (
            db.query(OnboardingDataset)
            .filter(
                OnboardingDataset.id == run_id,
                OnboardingDataset.tenant_id == tenant_id,
            )
            .first()
        )

        if staged is None:
            staged = OnboardingDataset(
                id=run_id,
                tenant_id=tenant_id,
                source_name=source_name,
                source_type=source_type.value,
                input_hash=input_hash,
                raw_payload_json=json.dumps(
                    records,
                    default=str,
                    sort_keys=True,
                ),
                source_columns_json=json.dumps(
                    source_columns or [],
                    default=str,
                ),
                detected_entity=detected_entity,
                status=status,
            )
            db.add(staged)
        else:
            staged.source_name = source_name
            staged.source_type = source_type.value
            staged.input_hash = input_hash
            staged.raw_payload_json = json.dumps(
                records,
                default=str,
                sort_keys=True,
            )
            staged.source_columns_json = json.dumps(
                source_columns or [],
                default=str,
            )
            staged.detected_entity = detected_entity
            staged.status = status

        db.flush()
        return staged

    @staticmethod
    def _persist_canonical_records(
        db: Session,
        tenant_id: str,
        entity_name: str,
        records: List[Dict[str, Any]],
        run_id: str,
    ) -> Tuple[int, Optional[str]]:
        """
        Persist accepted canonical records through the explicit tenant-scoped
        CanonicalMapper.

        Returns:
            (persisted_count, persistence_error)
        """
        if not records:
            return 0, None

        mapper = CanonicalMapper(db=db, tenant_id=tenant_id)
        frame = pd.DataFrame(records)

        if entity_name == "inventory_movement_history":
            return 0, (
                "Monthly inventory movement history was recognized and "
                "normalized, but no location_id is present. "
                "Operational inventory-position persistence requires an "
                "explicit location mapping."
            )

        dispatch = {
            "customers": mapper.map_customers,
            "orders": mapper.map_orders,
            "purchase_orders": mapper.map_purchase_orders,
            "shipments": mapper.map_shipments,
            "invoices": mapper.map_invoices,
            "work_orders": mapper.map_work_orders,

            # Existing canonical mappings.
            "inventory_levels": mapper.map_inventory,
            "supplier_profiles": mapper.map_suppliers,
            "network_nodes": mapper.map_locations,
            "item_costs": mapper.map_products,

            # These currently have no safe operational ORM destination.
            "demand_history": None,
            "boms": None,
        }

        handler = dispatch.get(entity_name)

        if handler is None:
            return 0, (
                f"Canonical persistence is not implemented for "
                f"entity '{entity_name}'."
            )

        if not callable(handler):
            return 0, (
                f"Entity '{entity_name}' was recognized by onboarding, "
                "but no safe canonical persistence target exists yet."
            )

        try:
            persisted = int(handler(frame, run_id))
            return persisted, None
        except Exception as exc:
            db.rollback()
            logger.exception(
                "Canonical persistence failed for %s / %s.",
                entity_name,
                run_id,
            )
            return 0, str(exc)

    @staticmethod
    def _update_staged_status(
        staged: Optional[OnboardingDataset],
        status: str,
        detected_entity: Optional[str] = None,
    ) -> None:
        if staged is None:
            return

        staged.status = status

        if detected_entity is not None:
            staged.detected_entity = detected_entity

    @staticmethod
    def _transform_to_canonical(
        records: List[Dict[str, Any]],
        accepted_mappings: Dict[str, str],
    ) -> List[Dict[str, Any]]:
        """Transforms source record dictionary keys into canonical field names."""
        canonical_records: List[Dict[str, Any]] = []

        for row in records:
            canon_row: Dict[str, Any] = {}

            for src_col, canon_field in accepted_mappings.items():
                if src_col in row:
                    canon_row[canon_field] = row[src_col]

            canonical_records.append(canon_row)

        return canonical_records

    @staticmethod
    def _resolve_onboarding_freshness(
        source_type: SourceType,
    ) -> str:
        """
        Resolve onboarding freshness without inventing business freshness.

        A newly received file/API payload proves only that AURIX received
        the source successfully. It does not prove that the underlying
        business data is currently fresh.

        Therefore UNKNOWN is the safe default until authoritative source
        timestamp metadata exists.
        """
        _ = source_type
        return "UNKNOWN"

    @staticmethod
    def _unknown_entity_result(
        run_id: str,
        tenant_id: str,
        input_hash: str,
        source_type: SourceType,
        source_name: str,
        records_received: int,
        discovery_report: Any,
    ) -> OnboardingResult:
        """
        Return a controlled user-input state when AURIX cannot safely
        determine the business entity represented by the dataset.
        """
        return OnboardingResult(
            run_id=run_id,
            tenant_id=tenant_id,
            input_hash=input_hash,
            source_type=source_type,
            source_name=source_name,
            records_received=records_received,
            schema_discovery=discovery_report,
            warnings=[
                (
                    "AURIX could not deterministically identify the "
                    "business dataset/entity represented by the supplied "
                    "data. No analytical capability was activated."
                )
            ],
            overall_status=OnboardingStatus.USER_INPUT_REQUIRED,
            next_required_input="CONFIRM_DATASET_ENTITY",
            freshness="UNKNOWN",
            provenance={
                "entity_detection": "UNRESOLVED",
                "capability_execution_blocked": True,
                "freshness_basis": (
                    "No authoritative source timestamp supplied."
                ),
            },
        )

    @classmethod
    def _evaluate_capabilities_and_merge(
        cls,
        tenant_id: str,
        entity_name: str,
        canonical_records: List[Dict[str, Any]],
        existing_records: Optional[List[Dict[str, Any]]] = None,
    ) -> Tuple[
        CapabilityOnboardingSummary,
        DuplicateCorrectionStatus,
        List[str],
        List[Dict[str, Any]],
    ]:
        """
        Executes incremental merge diffing and evaluates available
        downstream capabilities.

        Returns:
            (
                capability_summary,
                duplicate_status,
                affected_capabilities,
                merged_records,
            )
        """
        _ = tenant_id

        merge_result: MergeResult = (
            IncrementalMergeEngine.merge_dataset(
                existing_records=existing_records or [],
                new_records=canonical_records,
                entity_name=entity_name,
            )
        )

        dup_status = (
            DuplicateCorrectionStatus.NO_DUPLICATES
        )

        if merge_result.is_duplicate:
            dup_status = (
                DuplicateCorrectionStatus.DUPLICATE_IDENTICAL
            )
        elif merge_result.corrections_count > 0:
            dup_status = (
                DuplicateCorrectionStatus.HISTORICAL_CORRECTION
            )
        elif merge_result.appended_count > 0:
            dup_status = (
                DuplicateCorrectionStatus.INCREMENTAL_APPEND
            )

        if entity_name == "demand_history":
            required_keys = [
                "sku_id",
                "date",
                "quantity",
            ]
        elif (
            canonical_records
            and "sku_id" in canonical_records[0]
        ):
            required_keys = ["sku_id"]
        else:
            required_keys = []

        readiness_map = {
            entity_name: (
                DataReadinessEngine.evaluate_entity_readiness(
                    entity_name=entity_name,
                    records=merge_result.merged_records,
                    required_fields=required_keys,
                )
            )
        }

        # Capability discovery requires the actual historical depth of the
        # merged dataset. Do not default to zero because doing so can block
        # otherwise eligible capabilities such as demand classification.
        history_depth_map: Dict[str, int] = {}

        if entity_name == "demand_history":
            history_dates = {
                str(record.get("date"))
                for record in merge_result.merged_records
                if record.get("date") is not None
            }
            history_depth_map[entity_name] = len(history_dates)

        discovery = (
            CapabilityDiscoveryEngine.discover(
                readiness_map=readiness_map,
                history_depth_map=history_depth_map,
            )
        )

        available_caps: List[str] = []
        partial_caps: List[str] = []
        unavailable_caps: List[str] = []

        for name, cap in discovery.capabilities.items():
            status_val = getattr(
                cap.status,
                "value",
                str(cap.status),
            )

            if status_val in ("AVAILABLE", "STALE_DATA"):
                available_caps.append(name)
            elif status_val == "PARTIAL":
                partial_caps.append(name)
            else:
                unavailable_caps.append(name)

        # Do not manually unlock demand capabilities here.
        #
        # CapabilityDiscoveryEngine is the single authority for whether
        # a capability is actually eligible.
        prereqs: Dict[str, List[str]] = {
            name: cap.missing_prerequisites
            for name, cap in discovery.capabilities.items()
            if cap.missing_prerequisites
        }

        cap_summary = CapabilityOnboardingSummary(
            available_capabilities=available_caps,
            partial_capabilities=partial_caps,
            unavailable_capabilities=unavailable_caps,
            prerequisites_needed=prereqs,
        )

        return (
            cap_summary,
            dup_status,
            merge_result.affected_capabilities,
            merge_result.merged_records,
        )

    @staticmethod
    def _normalize_workbook_header(value: Any) -> str:
        """Normalize workbook headers for structural profile detection."""
        return (
            str(value)
            .strip()
            .lower()
            .replace("_", "")
            .replace("-", "")
            .replace(" ", "")
        )

    @classmethod
    def _detect_monthly_inventory_ledger(
        cls,
        workbook_sheets: List[Tuple[str, List[Dict[str, Any]], List[str]]],
    ) -> bool:
        """
        Detects a repeated monthly inventory movement ledger.

        Expected repeated structure:
            Particulars
            Opening Balance
            Inwards
            Outwards
            Closing Balance

        Sheet names are expected to contain a month/year signal such as
        APRIL24, MAY24, ... MARCH26.
        """
        if len(workbook_sheets) < 2:
            return False

        required_signature = {
            "particulars",
            "openingbalance",
            "inwards",
            "outwards",
            "closingbalance",
        }

        month_tokens = {
            "JAN", "JANUARY",
            "FEB", "FEBRUARY",
            "MAR", "MARCH",
            "APR", "APRIL",
            "MAY",
            "JUN", "JUNE",
            "JUL", "JULY",
            "AUG", "AUGUST",
            "SEP", "SEPTEMBER",
            "OCT", "OCTOBER",
            "NOV", "NOVEMBER",
            "DEC", "DECEMBER",
        }

        matched_sheets = 0

        for sheet_name, _records, columns in workbook_sheets:
            normalized_columns = {
                cls._normalize_workbook_header(column)
                for column in columns
            }

            if not required_signature.issubset(normalized_columns):
                return False

            upper_name = str(sheet_name).strip().upper()

            has_month = any(
                token in upper_name
                for token in month_tokens
            )

            has_year = any(
                str(year) in upper_name
                for year in range(20, 40)
            )

            if not (has_month and has_year):
                return False

            matched_sheets += 1

        return matched_sheets == len(workbook_sheets)

    @classmethod
    def _transform_monthly_inventory_ledger(
        cls,
        workbook_sheets: List[Tuple[str, List[Dict[str, Any]], List[str]]],
    ) -> Tuple[
        List[Dict[str, Any]],
        List[str],
        Dict[str, Any],
    ]:
        """
        Converts repeated monthly inventory ledger sheets into a canonical
        inventory-movement representation without inventing location data.
        """
        combined_records: List[Dict[str, Any]] = []
        warnings: List[str] = []
        sheet_details: List[Dict[str, Any]] = []

        column_aliases = {
            "particulars": "sku_id",
            "openingbalance": "opening_balance",
            "inwards": "inbound_quantity",
            "outwards": "outbound_quantity",
            "closingbalance": "on_hand",
        }

        for sheet_name, sheet_records, columns in workbook_sheets:
            normalized_to_source = {
                cls._normalize_workbook_header(column): column
                for column in columns
            }

            missing = [
                key
                for key in column_aliases
                if key not in normalized_to_source
            ]

            if missing:
                warnings.append(
                    f"Sheet '{sheet_name}' is missing expected ledger "
                    f"columns: {missing}."
                )
                continue

            try:
                sheet_token = str(sheet_name).strip().upper()

                # Normalize known month-name typos found in enterprise
                # spreadsheet exports without modifying the source workbook.
                month_corrections = {
                    "OCTOMBER": "OCTOBER",
                }

                for bad_month, good_month in month_corrections.items():
                    if sheet_token.startswith(bad_month):
                        sheet_token = (
                            good_month
                            + sheet_token[len(bad_month):]
                        )
                        break

                parsed_period = pd.to_datetime(
                    sheet_token,
                    format="%B%y",
                    errors="coerce",
                )

                if pd.isna(parsed_period):
                    parsed_period = pd.to_datetime(
                        sheet_token,
                        format="%b%y",
                        errors="coerce",
                    )

                if pd.isna(parsed_period):
                    raise ValueError(
                        f"Unable to derive monthly period from sheet "
                        f"'{sheet_name}'."
                    )

                period_value = parsed_period.strftime(
                    "%Y-%m-01"
                )

            except Exception as exc:
                warnings.append(str(exc))
                continue

            transformed_count = 0

            for row_index, row in enumerate(sheet_records):
                sku_value = row.get(
                    normalized_to_source["particulars"]
                )

                if sku_value is None or str(sku_value).strip() == "":
                    continue

                transformed = {
                    "sku_id": str(sku_value).strip(),
                    "period": period_value,
                    "opening_balance": row.get(
                        normalized_to_source["openingbalance"]
                    ),
                    "inbound_quantity": row.get(
                        normalized_to_source["inwards"]
                    ),
                    "outbound_quantity": row.get(
                        normalized_to_source["outwards"]
                    ),
                    "on_hand": row.get(
                        normalized_to_source["closingbalance"]
                    ),
                    "source_sheet": str(sheet_name),
                    "source_record_id": (
                        f"{sheet_name}:{row_index + 1}"
                    ),
                }

                combined_records.append(transformed)
                transformed_count += 1

            sheet_details.append(
                {
                    "sheet_name": str(sheet_name),
                    "period": period_value,
                    "record_count": transformed_count,
                }
            )

        return combined_records, warnings, {
            "dataset_type": "inventory_movement_history",
            "sheet_count": len(workbook_sheets),
            "sheet_details": sheet_details,
        }

    @classmethod
    def onboard_file(
        cls,
        db: Session,
        tenant_id: str,
        filename: str,
        content: bytes,
        source_type_override: Optional[SourceType] = None,
        existing_records: Optional[
            List[Dict[str, Any]]
        ] = None,
    ) -> OnboardingResult:
        """End-to-end automated onboarding pipeline for raw customer files."""
        run_id = (
            f"ONBOARD-"
            f"{uuid.uuid4().hex[:10].upper()}"
        )

        input_hash = cls._compute_input_hash(
            content
        )

        try:
            (
                clean_name,
                detected_source_type,
            ) = FileSafetyValidator.validate_file(
                filename,
                content,
            )

            source_type = (
                source_type_override
                or detected_source_type
            )

        except FileSafetyException as exc:
            return OnboardingResult(
                run_id=run_id,
                tenant_id=tenant_id,
                input_hash=input_hash,
                source_type=(
                    source_type_override
                    or SourceType.CSV
                ),
                source_name=filename,
                warnings=[
                    f"Safety rejection: {exc.message}"
                ],
                overall_status=(
                    OnboardingStatus.FAILED
                ),
                freshness="UNKNOWN",
                provenance={
                    "freshness_basis": (
                        "No business freshness can be "
                        "established from rejected input."
                    ),
                },
            )

        normalization_warnings: List[str] = []
        normalization_stats: Dict[str, int] = {}
        workbook_sheet_details: List[Dict[str, Any]] = []
        specialized_workbook_profile: Optional[Dict[str, Any]] = None

        try:
            if source_type == SourceType.XLSX:
                workbook_sheets = DataParser.parse_xlsx_workbook(content)

                if cls._detect_monthly_inventory_ledger(workbook_sheets):
                    (
                        ledger_records,
                        ledger_warnings,
                        ledger_profile,
                    ) = cls._transform_monthly_inventory_ledger(
                        workbook_sheets
                    )

                    records = ledger_records
                    columns = [
                        "sku_id",
                        "period",
                        "opening_balance",
                        "inbound_quantity",
                        "outbound_quantity",
                        "on_hand",
                        "source_sheet",
                        "source_record_id",
                    ]

                    normalization_warnings.extend(
                        ledger_warnings
                    )

                    # Keep workbook-level metadata available to the
                    # onboarding response.
                    workbook_sheet_details = ledger_profile.get(
                        "sheet_details",
                        [],
                    )

                    specialized_workbook_profile = ledger_profile

                    # This dataset has a deterministic business profile.
                    # Do not force it through the generic per-sheet merge
                    # path because it is not a conventional inventory snapshot.
                elif len(workbook_sheets) > 1:
                    combined_canonical_records: List[Dict[str, Any]] = []
                    reports: List[Tuple[str, Any, Dict[str, str], List[Dict[str, Any]]]] = []
                    detected_entities: Set[str] = set()
                    unresolved_sheets: List[str] = []

                    for sheet_name, sheet_records, sheet_columns in workbook_sheets:
                        normalized_records, sheet_warnings, sheet_stats = (
                            EnterpriseNormalizationEngine.normalize_records(sheet_records)
                        )
                        normalization_warnings.extend(
                            [f"Sheet '{sheet_name}': {warning}" for warning in sheet_warnings]
                        )
                        for key, value in sheet_stats.items():
                            normalization_stats[key] = normalization_stats.get(key, 0) + value

                        report = SchemaDiscoveryEngine.discover_schema(
                            normalized_records,
                            source_columns=sheet_columns,
                        )
                        report, mappings = SemanticMapper.map_schema(report)
                        entity = report.detected_entity_name
                        confidence = float(report.entity_confidence)

                        workbook_sheet_details.append({
                            "sheet_name": sheet_name,
                            "record_count": len(normalized_records),
                            "entity": entity,
                            "entity_confidence": confidence,
                            "ambiguous_columns": report.ambiguous_columns,
                        })

                        if not entity or report.ambiguous_columns:
                            unresolved_sheets.append(sheet_name)
                        else:
                            detected_entities.add(str(entity))
                            reports.append((sheet_name, report, mappings, normalized_records))

                    if unresolved_sheets or len(detected_entities) != 1:
                        return OnboardingResult(
                            run_id=run_id,
                            tenant_id=tenant_id,
                            input_hash=input_hash,
                            source_type=source_type,
                            source_name=clean_name,
                            records_received=sum(len(x[1]) for x in workbook_sheets),
                            warnings=(
                                normalization_warnings
                                + [
                                    (
                                        "Workbook contains multiple sheets requiring "
                                        "explicit classification or mapping before AURIX "
                                        f"can safely merge them. Sheets requiring input: {unresolved_sheets or 'none'}."
                                    )
                                ]
                            ),
                            overall_status=OnboardingStatus.USER_INPUT_REQUIRED,
                            next_required_input="CONFIRM_WORKBOOK_SHEET_MAPPING",
                            freshness="UNKNOWN",
                            provenance={
                                "workbook_sheet_details": workbook_sheet_details,
                                "detected_entities": sorted(detected_entities),
                                "capability_execution_blocked": True,
                                "normalization_stats": normalization_stats,
                            },
                        )

                    primary_report = reports[0][1]
                    canonical_columns: Set[str] = set()
                    for _sheet_name, report, mappings, sheet_records in reports:
                        canonical = cls._transform_to_canonical(sheet_records, mappings)
                        combined_canonical_records.extend(canonical)
                        canonical_columns.update(mappings.values())

                    primary_report.source_columns = sorted(canonical_columns)
                    primary_report.total_columns_detected = len(primary_report.source_columns)
                    primary_report.sample_record_count = len(combined_canonical_records)
                    primary_report.total_records = len(combined_canonical_records)

                    records = combined_canonical_records
                    columns = primary_report.source_columns
                    discovery_report = primary_report
                    accepted_mappings = {
                        field: field for field in canonical_columns
                    }
                    workbook_merged = True
                else:
                    records, columns = DataParser.parse_xlsx(content)
                    records, normalization_warnings, normalization_stats = (
                        EnterpriseNormalizationEngine.normalize_records(records)
                    )
                    workbook_merged = False
            else:
                records, columns = DataParser.parse(source_type, content)
                if source_type == SourceType.API:
                    normalization_warnings = []
                    normalization_stats = {}
                else:
                    records, normalization_warnings, normalization_stats = (
                        EnterpriseNormalizationEngine.normalize_records(records)
                    )
                workbook_merged = False

        except Exception as exc:
            logger.exception(
                "File parsing failed for onboarding run %s.",
                run_id,
            )

            return OnboardingResult(
                run_id=run_id,
                tenant_id=tenant_id,
                input_hash=input_hash,
                source_type=source_type,
                source_name=clean_name,
                warnings=[
                    f"File parsing failure: {exc}"
                ],
                overall_status=(
                    OnboardingStatus.FAILED
                ),
                freshness="UNKNOWN",
                provenance={
                    "freshness_basis": (
                        "Parsing failed; source freshness "
                        "could not be established."
                    ),
                },
            )

        if not records:
            return OnboardingResult(
                run_id=run_id,
                tenant_id=tenant_id,
                input_hash=input_hash,
                source_type=source_type,
                source_name=clean_name,
                warnings=[
                    (
                        "Dataset contains no valid records "
                        "after header extraction."
                    )
                ],
                overall_status=(
                    OnboardingStatus.FAILED
                ),
                freshness="UNKNOWN",
                provenance={
                    "freshness_basis": (
                        "No valid records were received."
                    ),
                },
            )

        staged = cls._stage_dataset(
            db=db,
            tenant_id=tenant_id,
            run_id=run_id,
            source_name=clean_name,
            source_type=source_type,
            input_hash=input_hash,
            records=records,
            source_columns=columns,
            detected_entity=None,
            status="RECEIVED",
        )

        if specialized_workbook_profile is not None:
            discovery_report = SchemaDiscoveryEngine.discover_schema(
                records,
                source_columns=columns,
            )

            # Override generic entity detection with the deterministic
            # workbook profile. This prevents a monthly inventory ledger
            # from being misclassified as a conventional inventory snapshot.
            discovery_report.detected_entity_name = (
                "inventory_movement_history"
            )
            discovery_report.entity_confidence = 1.0

            specialized_fields = {
                "sku_id": "sku_id",
                "period": "period",
                "opening_balance": "opening_balance",
                "inbound_quantity": "inbound_quantity",
                "outbound_quantity": "outbound_quantity",
                "on_hand": "on_hand",
                "source_sheet": "source_sheet",
                "source_record_id": "source_record_id",
            }

            accepted_mappings = {
                source: canonical
                for source, canonical in specialized_fields.items()
                if source in columns
            }

            discovery_report.ambiguous_columns = []
            discovery_report.unmapped_columns = [
                column
                for column in columns
                if column not in accepted_mappings
            ]

            for source_column, canonical_field in accepted_mappings.items():
                if source_column in discovery_report.field_mappings:
                    mapping = discovery_report.field_mappings[source_column]
                    mapping.canonical_field = canonical_field
                    mapping.target_field = canonical_field
                    mapping.confidence_score = 1.0
                    mapping.is_ambiguous = False
                    mapping.ambiguity_reasons = []

        elif not locals().get("workbook_merged", False):
            discovery_report = (
                SchemaDiscoveryEngine.discover_schema(
                    records,
                    source_columns=columns,
                )
            )

            discovery_report, accepted_mappings = (
                SemanticMapper.map_schema(
                    discovery_report
                )
            )

        entity_name = (
            discovery_report.detected_entity_name
        )

        if discovery_report.ambiguous_columns:
            cls._update_staged_status(
                staged,
                "USER_INPUT_REQUIRED",
                entity_name,
            )
            db.commit()

            return OnboardingResult(
                run_id=run_id,
                tenant_id=tenant_id,
                input_hash=input_hash,
                source_type=source_type,
                source_name=clean_name,
                records_received=len(records),
                schema_discovery=discovery_report,
                warnings=[
                    (
                        "Ambiguous mapping detected on columns: "
                        f"{discovery_report.ambiguous_columns}. "
                        "Manual column confirmation required."
                    )
                ],
                overall_status=(
                    OnboardingStatus.USER_INPUT_REQUIRED
                ),
                next_required_input=(
                    "RESOLVE_MAPPING_AMBIGUITY"
                ),
                freshness="UNKNOWN",
                provenance={
                    "freshness_basis": (
                        "No authoritative source timestamp supplied."
                    ),
                },
            )

        cls._update_staged_status(
            staged,
            "USER_INPUT_REQUIRED" if not entity_name else "PROCESSING",
            entity_name,
        )
        db.flush()


        if not entity_name:
            return cls._unknown_entity_result(
                run_id=run_id,
                tenant_id=tenant_id,
                input_hash=input_hash,
                source_type=source_type,
                source_name=clean_name,
                records_received=len(records),
                discovery_report=discovery_report,
            )

        canonical_fields: Set[str] = set(
            accepted_mappings.values()
        )

        if locals().get("workbook_merged", False):
            canonical_records = records
        else:
            canonical_records = (
                cls._transform_to_canonical(
                    records,
                    accepted_mappings,
                )
            )

        (
            accepted,
            rejected,
            quality,
            temporal,
            completeness,
        ) = OnboardingQualityEngine.evaluate(
            records=canonical_records,
            entity_name=entity_name,
            mapped_fields=canonical_fields,
        )

        (
            cap_summary,
            dup_status,
            affected_caps,
            _merged_records,
        ) = cls._evaluate_capabilities_and_merge(
            tenant_id=tenant_id,
            entity_name=entity_name,
            canonical_records=accepted,
            existing_records=existing_records,
        )

        persisted_count, persistence_error = (
            cls._persist_canonical_records(
                db=db,
                tenant_id=tenant_id,
                entity_name=entity_name,
                records=accepted,
                run_id=run_id,
            )
        )

        # Persist rejected records into tenant-scoped quarantine storage before
        # writing the ingestion audit record. Raw rows are retained for review
        # and are never silently discarded.
        if rejected:
            try:
                for index, rejected_row in enumerate(rejected):
                    reason = "; ".join(
                        [
                            str(message)
                            for message in quality.error_breakdown.keys()
                        ]
                    ) or "ONBOARDING_VALIDATION_REJECTED"
                    row_hash = hashlib.sha256(
                        json.dumps(
                            rejected_row,
                            sort_keys=True,
                            default=str,
                        ).encode("utf-8")
                    ).hexdigest()
                    db.add(
                        OnboardingQuarantineRecord(
                            id=f"Q-{run_id}-{index:06d}",
                            tenant_id=tenant_id,
                            run_id=run_id,
                            row_hash=row_hash,
                            reason=reason,
                            payload_json=json.dumps(
                                rejected_row,
                                sort_keys=True,
                                default=str,
                            ),
                            created_at=datetime.now(timezone.utc),
                        )
                    )
                db.flush()
            except Exception as exc:
                db.rollback()
                logger.exception(
                    "Failed to persist onboarding quarantine records for %s.",
                    run_id,
                )
                raise RuntimeError(
                    f"Onboarding quarantine persistence failed for run '{run_id}'."
                ) from exc

        status = OnboardingStatus.COMPLETED

        # Persistence is mandatory only for entities with an explicit,
        # safe operational ORM destination. Analytical entities such as
        # demand_history may be successfully onboarded and evaluated even
        # when no canonical operational persistence target exists yet.
        persistence_required_entities = {
            "customers",
            "orders",
            "purchase_orders",
            "shipments",
            "invoices",
            "work_orders",
            "inventory_levels",
            "supplier_profiles",
            "network_nodes",
            "item_costs",
        }

        persistence_required = (
            entity_name in persistence_required_entities
        )

        if persistence_required and (
            persistence_error is not None
            or persisted_count != len(accepted)
        ):
            status = OnboardingStatus.PARTIAL_SUCCESS

        # A recognized historical inventory ledger is intentionally not
        # persisted into inventory_positions without an explicit location.
        # Preserve the successful onboarding result while exposing the
        # persistence limitation to the caller.
        if entity_name == "inventory_movement_history":
            status = (
                OnboardingStatus.COMPLETED
                if len(rejected) == 0
                else OnboardingStatus.PARTIAL_SUCCESS
            )

        if (
            dup_status
            == DuplicateCorrectionStatus.DUPLICATE_IDENTICAL
        ):
            status = OnboardingStatus.DUPLICATE

        elif (
            len(rejected) > 0
            or len(cap_summary.partial_capabilities) > 0
        ):
            status = OnboardingStatus.PARTIAL_SUCCESS

        # Update the durable staging state BEFORE the final transaction commit.
        cls._update_staged_status(
            staged,
            status.value,
            entity_name,
        )

        # Persist ingestion audit record using the actual ORM contract.
        #
        # IngestionRun does not expose run_id/input_hash/records_processed.
        # Its canonical fields are id/data_hash/record_count/error_count/
        # validation_summary.
        try:
            run_rec = IngestionRun(
                id=run_id,
                tenant_id=tenant_id,
                source_name=clean_name,
                domain=entity_name,
                status=(
                    "COMPLETED"
                    if (
                        len(rejected) == 0
                        and (
                            not persistence_required
                            or (
                                persisted_count == len(accepted)
                                and persistence_error is None
                            )
                        )
                    )
                    else "PARTIAL_SUCCESS"
                ),
                data_hash=input_hash,
                record_count=len(records),
                error_count=(
                    len(rejected)
                    + max(0, len(accepted) - persisted_count)
                ),
                validation_summary=json.dumps(
                    {
                        "records_received": len(records),
                        "records_accepted": len(accepted),
                        "records_rejected": len(rejected),
                        "records_persisted": persisted_count,
                        "persistence_error": persistence_error,
                        "quality": quality,
                        "completeness": completeness,
                        "temporal_coverage": temporal,
                    },
                    default=str,
                    sort_keys=True,
                ),
                completed_at=datetime.now(timezone.utc),
            )

            db.add(run_rec)

            # One final transaction commit makes the operational rows,
            # staging state, and ingestion audit atomically durable.
            db.commit()

        except Exception:
            db.rollback()

            logger.exception(
                "Failed to persist ingestion audit run %s.",
                run_id,
            )
            raise

        freshness = (
            cls._resolve_onboarding_freshness(
                source_type
            )
        )

        return OnboardingResult(
            run_id=run_id,
            tenant_id=tenant_id,
            input_hash=input_hash,
            source_type=source_type,
            source_name=clean_name,
            records_received=len(records),
            records_accepted=len(accepted),
            records_rejected=len(rejected),
            preview_records=[
                {
                    str(key): value
                    for key, value in row.items()
                }
                for row in records[:10]
            ],
            warnings=(
                normalization_warnings
                + ([
                    (
                        f"Rejected {len(rejected)} records "
                        "due to validation errors."
                    )
                ] if rejected else [])
                + ([
                    (
                        f"Persisted {persisted_count} of "
                        f"{len(accepted)} accepted records."
                    )
                ] if persisted_count != len(accepted) else [])
                + ([
                    f"Persistence warning: {persistence_error}"
                ] if persistence_error else [])
            ),
            quality_summary=quality,
            completeness_summary=completeness,
            temporal_coverage=temporal,
            schema_discovery=discovery_report,
            capability_summary=cap_summary,
            duplicate_status=dup_status,
            correction_status=dup_status,
            recomputed_capabilities=affected_caps,
            freshness=freshness,
            overall_status=status,
            provenance={
                "detected_entity": entity_name,
                "mappings_applied": accepted_mappings,
                "input_hash": input_hash,
                "freshness_basis": (
                    "Upload receipt time only; source business "
                    "freshness not supplied."
                ),
                "received_at": (
                    datetime.now(
                        timezone.utc
                    ).isoformat()
                ),
                "source_timestamp": None,
            },
        )

    @classmethod
    def onboard_raw_records(
        cls,
        db: Session,
        tenant_id: str,
        records: List[Dict[str, Any]],
        source_name: str = "API_PAYLOAD",
        existing_records: Optional[
            List[Dict[str, Any]]
        ] = None,
    ) -> OnboardingResult:
        """Direct onboarding pipeline for in-memory JSON arrays and API payloads."""
        content_bytes = json.dumps(
            records,
            default=str,
        ).encode("utf-8")

        return cls.onboard_file(
            db=db,
            tenant_id=tenant_id,
            filename=f"{source_name}.json",
            content=content_bytes,
            source_type_override=SourceType.API,
            existing_records=existing_records,
        )

    @classmethod
    def resolve_manual_mapping(
        cls,
        db: Session,
        tenant_id: str,
        raw_records: List[Dict[str, Any]],
        request_data: ManualMappingResolutionRequest,
        existing_records: Optional[
            List[Dict[str, Any]]
        ] = None,
    ) -> OnboardingResult:
        """Resumes an onboarding execution by applying client-provided column mapping overrides."""
        OnboardingService._bind_tenant_to_session(db, tenant_id)
        run_id = request_data.run_id

        staged = (
            db.query(OnboardingDataset)
            .filter(
                OnboardingDataset.id == run_id,
                OnboardingDataset.tenant_id == tenant_id,
            )
            .first()
        )

        if staged is not None:
            staged_records = json.loads(staged.raw_payload_json)
            raw_records = staged_records
            input_hash = staged.input_hash
            source_name = staged.source_name
            source_type = (
                SourceType(staged.source_type)
                if staged.source_type in SourceType._value2member_map_
                else SourceType.API
            )
        elif not raw_records:
            return OnboardingResult(
                run_id=run_id,
                tenant_id=tenant_id,
                input_hash=None,
                source_type=SourceType.API,
                source_name="MANUAL_RESOLUTION",
                records_received=0,
                warnings=[
                    (
                        f"No staged onboarding dataset found for run "
                        f"'{run_id}'."
                    )
                ],
                overall_status=OnboardingStatus.FAILED,
                freshness="UNKNOWN",
            )
        else:
            input_hash = hashlib.sha256(
                json.dumps(
                    raw_records,
                    default=str,
                ).encode("utf-8")
            ).hexdigest()
            source_name = "MANUAL_RESOLUTION"
            source_type = SourceType.API

        discovery_report = (
            SchemaDiscoveryEngine.discover_schema(
                raw_records
            )
        )

        (
            discovery_report,
            accepted_mappings,
        ) = SemanticMapper.apply_manual_overrides(
            discovery_report=discovery_report,
            manual_mappings=request_data.resolved_mappings,
        )

        entity_name = (
            request_data.override_entity_name
            or discovery_report.detected_entity_name
        )

        if not entity_name:
            return OnboardingResult(
                run_id=run_id,
                tenant_id=tenant_id,
                input_hash=input_hash,
                source_type=SourceType.API,
                source_name="MANUAL_RESOLUTION",
                records_received=len(raw_records),
                schema_discovery=discovery_report,
                warnings=[
                    (
                        "Manual field mapping was accepted, but the "
                        "business dataset/entity remains unresolved. "
                        "Specify override_entity_name before analytical "
                        "capabilities can be activated."
                    )
                ],
                overall_status=(
                    OnboardingStatus.USER_INPUT_REQUIRED
                ),
                next_required_input=(
                    "CONFIRM_DATASET_ENTITY"
                ),
                freshness="UNKNOWN",
                provenance={
                    "resolved_manually": True,
                    "mappings_applied": accepted_mappings,
                    "entity_detection": "UNRESOLVED",
                    "freshness_basis": (
                        "No authoritative source timestamp supplied."
                    ),
                },
            )

        canonical_fields: Set[str] = set(
            accepted_mappings.values()
        )

        canonical_records = (
            cls._transform_to_canonical(
                raw_records,
                accepted_mappings,
            )
        )

        (
            accepted,
            rejected,
            quality,
            temporal,
            completeness,
        ) = OnboardingQualityEngine.evaluate(
            records=canonical_records,
            entity_name=entity_name,
            mapped_fields=canonical_fields,
        )

        (
            cap_summary,
            dup_status,
            affected_caps,
            _merged_records,
        ) = cls._evaluate_capabilities_and_merge(
            tenant_id=tenant_id,
            entity_name=entity_name,
            canonical_records=accepted,
            existing_records=existing_records,
        )

        persisted_count, persistence_error = (
            cls._persist_canonical_records(
                db=db,
                tenant_id=tenant_id,
                entity_name=entity_name,
                records=accepted,
                run_id=run_id,
            )
        )

        persistence_required_entities = {
            "customers",
            "orders",
            "purchase_orders",
            "shipments",
            "invoices",
            "work_orders",
            "inventory_levels",
            "supplier_profiles",
            "network_nodes",
            "item_costs",
        }

        persistence_required = (
            entity_name in persistence_required_entities
        )

        status = (
            OnboardingStatus.COMPLETED
            if (
                len(rejected) == 0
                and (
                    not persistence_required
                    or (
                        persisted_count == len(accepted)
                        and persistence_error is None
                    )
                )
            )
            else OnboardingStatus.PARTIAL_SUCCESS
        )

        cls._update_staged_status(
            staged,
            status.value,
            entity_name,
        )

        return OnboardingResult(
            run_id=run_id,
            tenant_id=tenant_id,
            input_hash=input_hash,
            source_type=source_type,
            source_name=source_name,
            records_received=len(raw_records),
            records_accepted=len(accepted),
            records_rejected=len(rejected),
            warnings=(
                [
                    (
                        f"Rejected {len(rejected)} records "
                        "due to validation errors."
                    )
                ]
                if rejected
                else []
            )
            + (
                [
                    (
                        f"Persisted {persisted_count} of "
                        f"{len(accepted)} accepted records."
                    )
                ]
                if persisted_count != len(accepted)
                else []
            )
            + (
                [f"Persistence warning: {persistence_error}"]
                if persistence_error
                else []
            ),
            quality_summary=quality,
            completeness_summary=completeness,
            temporal_coverage=temporal,
            schema_discovery=discovery_report,
            capability_summary=cap_summary,
            duplicate_status=dup_status,
            correction_status=dup_status,
            recomputed_capabilities=affected_caps,
            freshness="UNKNOWN",
            overall_status=status,
            provenance={
                "resolved_manually": True,
                "mappings_applied": accepted_mappings,
                "override_entity": entity_name,
                "freshness_basis": (
                    "Manual mapping does not establish source "
                    "business freshness."
                ),
                "source_timestamp": None,
            },
        )
