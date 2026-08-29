"""Pydantic v2 data contracts, status enums, and reports for Phase 11 Automated Data Onboarding."""

from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator


class SourceType(str, Enum):
    """Supported tabular data file sources and protocols."""
    CSV = "CSV"
    XLSX = "XLSX"
    JSON = "JSON"
    GOOGLE_SHEETS = "GOOGLE_SHEETS"
    API = "API"


class OnboardingStatus(str, Enum):
    """Overall status classification for customer onboarding ingestion runs."""
    COMPLETED = "COMPLETED"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    USER_INPUT_REQUIRED = "USER_INPUT_REQUIRED"
    DUPLICATE = "DUPLICATE"
    FAILED = "FAILED"


class DuplicateCorrectionStatus(str, Enum):
    """Classification of incremental dataset differences."""
    NONE = "NONE"
    NO_DUPLICATES = "NONE"
    DUPLICATE_IDENTICAL = "DUPLICATE_IDENTICAL"
    HISTORICAL_CORRECTION = "HISTORICAL_CORRECTION"
    INCREMENTAL_APPEND = "INCREMENTAL_APPEND"


class MappingConfidence(str, Enum):
    """Confidence levels for autonomous semantic field mappings."""
    HIGH_CONFIDENCE = "HIGH_CONFIDENCE"
    MEDIUM_CONFIDENCE = "MEDIUM_CONFIDENCE"
    LOW_CONFIDENCE = "LOW_CONFIDENCE"
    UNRESOLVED = "UNRESOLVED"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    AMBIGUOUS = "AMBIGUOUS"
    UNMAPPED = "UNMAPPED"


class FieldMappingInfo(BaseModel):
    """Individual field mapping metadata supporting semantic mapper attributes."""
    source_column: str
    target_field: Optional[str] = None
    canonical_field: Optional[str] = None
    inferred_type: str = "string"
    confidence: MappingConfidence = MappingConfidence.UNMAPPED
    confidence_score: float = 0.0
    is_required: bool = False
    validation_status: str = "PENDING"
    sample_values: List[Any] = Field(default_factory=list)
    is_ambiguous: bool = False
    ambiguity_reasons: List[str] = Field(default_factory=list)

    def model_post_init(self, __context: Any) -> None:
        if self.target_field and not self.canonical_field:
            self.canonical_field = self.target_field
        elif self.canonical_field and not self.target_field:
            self.target_field = self.canonical_field


# Compatibility alias
FieldMapping = FieldMappingInfo


class SchemaDiscoveryReport(BaseModel):
    """Statistical schema inference and entity detection report."""
    source_columns: List[str] = Field(default_factory=list)
    total_columns_detected: int = 0
    sample_record_count: int = 0
    total_records: int = 0
    detected_entity_name: Optional[str] = "demand_history"
    entity_confidence: Union[float, MappingConfidence] = 1.0
    field_mappings: Dict[str, FieldMappingInfo] = Field(default_factory=dict)
    ambiguous_columns: List[str] = Field(default_factory=list)
    unmapped_columns: List[str] = Field(default_factory=list)

    @field_validator("entity_confidence", mode="before")
    @classmethod
    def parse_entity_confidence(cls, v: Any) -> float:
        """Coerces MappingConfidence enums or strings into equivalent float confidence scores."""
        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, MappingConfidence):
            if v in (MappingConfidence.HIGH_CONFIDENCE, MappingConfidence.HIGH):
                return 0.95
            if v in (MappingConfidence.MEDIUM_CONFIDENCE, MappingConfidence.MEDIUM):
                return 0.75
            if v in (MappingConfidence.LOW_CONFIDENCE, MappingConfidence.LOW):
                return 0.50
            return 0.25
        if isinstance(v, str):
            upper_v = v.upper()
            if "HIGH" in upper_v:
                return 0.95
            if "MEDIUM" in upper_v:
                return 0.75
            if "LOW" in upper_v:
                return 0.50
            return 0.25
        return 1.0


class DataQualitySummary(BaseModel):
    """Hygiene and validation error breakdown."""
    total_records: int = 0
    accepted_records: int = 0
    rejected_records: int = 0
    null_density_pct: float = 0.0
    quality_score: float = 1.0
    validation_errors_count: int = 0
    error_breakdown: Dict[str, int] = Field(default_factory=dict)


class TemporalCoverage(BaseModel):
    """Historical sequence continuity and period gap analysis."""
    min_date: Optional[str] = None
    max_date: Optional[str] = None
    total_periods_detected: int = 0
    period_frequency: str = "UNKNOWN"
    missing_periods: List[str] = Field(default_factory=list)
    has_out_of_order_records: bool = False
    is_partial_month: bool = False
    temporal_completeness_pct: float = 100.0


class CompletenessSummary(BaseModel):
    """Multi-dimensional schema, record, and domain completeness metrics."""
    schema_completeness_pct: float = 100.0
    record_completeness_pct: float = 100.0
    domain_completeness_pct: float = 100.0
    temporal_completeness_pct: float = 100.0
    missing_required_fields: List[str] = Field(default_factory=list)
    missing_optional_fields: List[str] = Field(default_factory=list)


class CapabilityOnboardingSummary(BaseModel):
    """Discovered portfolio capabilities and missing prerequisite requirements."""
    available_capabilities: List[str] = Field(default_factory=list)
    partial_capabilities: List[str] = Field(default_factory=list)
    unavailable_capabilities: List[str] = Field(default_factory=list)
    prerequisites_needed: Dict[str, List[str]] = Field(default_factory=dict)


class OnboardingResult(BaseModel):
    """Master result container returned by the onboarding pipeline."""
    run_id: str
    tenant_id: str
    input_hash: Optional[str] = None
    source_type: SourceType = SourceType.CSV
    source_name: str = "dataset.csv"
    records_received: int = 0
    records_accepted: int = 0
    records_rejected: int = 0
    warnings: List[str] = Field(default_factory=list)
    quality_summary: Optional[DataQualitySummary] = None
    completeness_summary: Optional[CompletenessSummary] = None
    temporal_coverage: Optional[TemporalCoverage] = None
    schema_discovery: Optional[SchemaDiscoveryReport] = None
    capability_summary: Optional[CapabilityOnboardingSummary] = None
    preview_records: List[Dict[str, Any]] = Field(default_factory=list)
    duplicate_status: DuplicateCorrectionStatus = DuplicateCorrectionStatus.NONE
    correction_status: DuplicateCorrectionStatus = DuplicateCorrectionStatus.NONE
    recomputed_capabilities: List[str] = Field(default_factory=list)
    freshness: str = "LIVE"
    overall_status: OnboardingStatus = OnboardingStatus.COMPLETED
    next_required_input: Optional[str] = None
    provenance: Dict[str, Any] = Field(default_factory=dict)


# Compatibility alias for routers and test suites
OnboardingReport = OnboardingResult


class ManualMappingResolutionRequest(BaseModel):
    """Payload to resolve ambiguous column mappings."""
    run_id: str
    resolved_mappings: Dict[str, str]
    override_entity_name: Optional[str] = None