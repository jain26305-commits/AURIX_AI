import {
  IngestionMetadata,
  ColumnMappingItem,
  DataInspectionRow,
  ValidationIssue,
} from '@/types/data-intake.types';
import { ApiClient } from '@/services/api/apiClient';

export interface ModuleReadinessItem {
  moduleKey: string;
  moduleName: string;
  status: 'READY' | 'PARTIAL' | 'NOT_CONFIGURED';
  scorePercent: number;
  description: string;
  missingPrerequisites: string[];
  unlockedRoute: string;
}

export interface CapabilityReadinessReport {
  evaluatedAt: string;
  overallPlatformReadinessPercent: number;
  modules: ModuleReadinessItem[];
}

export interface FreshnessTelemetry {
  connectorId: string;
  state:
    | 'LIVE'
    | 'RECENT'
    | 'SYNCING'
    | 'DELAYED'
    | 'STALE'
    | 'DEGRADED'
    | 'OFFLINE';
  ageSeconds: number;
  lastSyncAt: string | null;
  isWithinSla: boolean;
  summary: string;
}

export interface QuarantinedItem {
  quarantineId: string;
  sourceSystem: string;
  sourceEntity: string;
  failureStage: string;
  failureReason: string;
  errorCode: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  resolved: boolean;
  createdAt: string;
}

interface BackendFieldMapping {
  source_column: string;
  target_field?: string | null;
  canonical_field?: string | null;
  inferred_type?: string;
  confidence?: string;
  confidence_score?: number;
  is_required?: boolean;
  validation_status?: string;
  sample_values?: unknown[];
  is_ambiguous?: boolean;
  ambiguity_reasons?: string[];
}

interface BackendOnboardingResult {
  run_id: string;
  tenant_id: string;
  input_hash?: string | null;
  source_type?: string;
  source_name: string;
  records_received: number;
  records_accepted: number;
  records_rejected: number;
  warnings?: string[];
  quality_summary?: {
    total_records?: number;
    accepted_records?: number;
    rejected_records?: number;
    null_density_pct?: number;
    quality_score?: number;
    validation_errors_count?: number;
    error_breakdown?: Record<string, number>;
  } | null;
  completeness_summary?: {
    schema_completeness_pct?: number;
    record_completeness_pct?: number;
    domain_completeness_pct?: number;
    temporal_completeness_pct?: number;
    missing_required_fields?: string[];
    missing_optional_fields?: string[];
  } | null;
  temporal_coverage?: unknown;
  schema_discovery?: {
    source_columns?: string[];
    total_columns_detected?: number;
    sample_record_count?: number;
    total_records?: number;
    detected_entity_name?: string | null;
    field_mappings?: Record<string, BackendFieldMapping>;
    ambiguous_columns?: string[];
    unmapped_columns?: string[];
  } | null;
  capability_summary?: unknown;
  duplicate_status?: string;
  correction_status?: string;
  recomputed_capabilities?: string[];
  freshness?: string;
  overall_status?: string;
  next_required_input?: string | null;
  provenance?: Record<string, unknown>;
  preview_records?: DataInspectionRow[];
}

export class IntakeService {
  public static async uploadOperationalData(file: File): Promise<{
    metadata: IngestionMetadata;
    mappings: ColumnMappingItem[];
    previewRows: DataInspectionRow[];
    validationIssues: ValidationIssue[];
  }> {
    const formData = new FormData();
    formData.append('file', file);

    const result = await ApiClient.upload<BackendOnboardingResult>(
      '/onboarding/upload',
      formData,
    );

    const fieldMappings = result.schema_discovery?.field_mappings ?? {};

    const mappings: ColumnMappingItem[] = Object.entries(fieldMappings).map(
      ([sourceColumn, mapping]) => {
        const canonicalKey =
          mapping.canonical_field ??
          mapping.target_field ??
          'UNMAPPED';

        const confidenceScore = mapping.confidence_score ?? 0;

        let confidence: ColumnMappingItem['confidence'] = 'unmapped';

        if (confidenceScore >= 0.88) {
          confidence = 'high';
        } else if (confidenceScore >= 0.65) {
          confidence = 'medium';
        } else if (confidenceScore >= 0.40) {
          confidence = 'low';
        }

        if (mapping.is_ambiguous) {
          confidence = 'unmapped';
        }

        const required = Boolean(mapping.is_required);

        return {
          canonicalKey,
          canonicalLabel: canonicalKey,
          canonicalName: canonicalKey,
          dataType: mapping.inferred_type,
          detectedColumn: sourceColumn,
          confidence,
          required,
          sampleValue:
            mapping.sample_values && mapping.sample_values.length > 0
              ? (mapping.sample_values[0] as string | number | null)
              : null,
          status: mapping.is_ambiguous
            ? 'warning'
            : canonicalKey === 'UNMAPPED'
              ? required
                ? 'missing'
                : 'warning'
              : 'valid',
        };
      },
    );

    const warnings = result.warnings ?? [];

    const validationIssues: ValidationIssue[] = warnings.map(
      (message, index) => ({
        id: `ONBOARDING-${index + 1}`,
        severity: 'WARNING',
        message,
      }),
    );

    const metadata: IngestionMetadata = {
      fileId: result.run_id,
      fileName: result.source_name || file.name,
      fileSize: `${(file.size / 1024).toFixed(1)} KB`,
      fileSizeBytes: file.size,
      rowCount: result.records_received,
      columnCount:
        result.schema_discovery?.total_columns_detected ??
        result.schema_discovery?.source_columns?.length ??
        0,
      detectedDatasetType:
        result.schema_discovery?.detected_entity_name ?? undefined,
      detectedDomain:
        result.schema_discovery?.detected_entity_name ?? undefined,
      uploadedAt: new Date().toISOString(),
      checksum: result.input_hash ?? undefined,
    };

    return {
      metadata,
      mappings,
      previewRows: result.preview_records ?? [],
      validationIssues,
    };
  }

  /**
   * Resolve mappings through the real onboarding endpoint.
   *
   * NOTE:
   * The current backend endpoint requires raw_records as well as
   * resolved_mappings. The present UI does not retain the original raw
   * records, so this function is intentionally not sufficient for actual
   * persistence yet. The backend persistence work must be completed next.
   */
  public static async commitMappings(
    runId: string,
    mappings: ColumnMappingItem[],
  ): Promise<boolean> {
    const resolvedMappings = mappings.reduce<Record<string, string>>(
      (acc, item) => {
        if (item.detectedColumn && item.canonicalKey !== 'UNMAPPED') {
          // Backend expects: source column -> canonical field
          acc[item.detectedColumn] = item.canonicalKey;
        }
        return acc;
      },
      {},
    );

    const response = await ApiClient.post<
      {
        raw_records: DataInspectionRow[];
        resolution: {
          run_id: string;
          resolved_mappings: Record<string, string>;
        };
      },
      BackendOnboardingResult
    >('/onboarding/resolve-mapping', {
      // The backend now resolves the durable staged dataset by run_id.
      // No browser-side copy of the original raw records is required.
      raw_records: [],
      resolution: {
        run_id: runId,
        resolved_mappings: resolvedMappings,
      },
    });

    return (
      response.overall_status === 'COMPLETED' ||
      response.overall_status === 'PARTIAL_SUCCESS'
    );
  }

  public static async getCapabilityReadiness(): Promise<CapabilityReadinessReport> {
    return ApiClient.get<CapabilityReadinessReport>('/data/readiness');
  }

  public static async getConnectorFreshness(
    connectorId: string,
  ): Promise<FreshnessTelemetry> {
    return ApiClient.get<FreshnessTelemetry>(
      `/integrations/connectors/${connectorId}/freshness`,
    );
  }

  public static async getQuarantinedRecords(): Promise<QuarantinedItem[]> {
    return ApiClient.get<QuarantinedItem[]>('/data/quarantine');
  }

  public static async replayQuarantineRecord(
    quarantineId: string,
  ): Promise<boolean> {
    const res = await ApiClient.post<
      { quarantineId: string },
      { replayed: boolean }
    >(`/data/quarantine/${quarantineId}/replay`, {
      quarantineId,
    });

    return res.replayed;
  }
}