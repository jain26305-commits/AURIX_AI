export type IssueSeverity =
  | 'ERROR'
  | 'WARNING'
  | 'INFO'
  | 'critical'
  | 'warning'
  | 'info';

export type ConfidenceLevel =
  | 'HIGH'
  | 'MEDIUM'
  | 'LOW'
  | 'exact'
  | 'high'
  | 'medium'
  | 'low'
  | 'suggested'
  | 'manual'
  | 'unmapped';

export interface CanonicalFieldDefinition {
  canonicalKey: string;
  canonicalName?: string;
  canonicalLabel?: string;
  required: boolean;
  dataType?: string;
  description?: string;
  synonyms?: string[];
  [key: string]: unknown;
}

export interface IngestionMetadata {
  fileId: string;
  fileName: string;
  fileSize?: string;
  fileSizeBytes: number;
  rowCount: number;
  columnCount?: number;
  detectedDatasetType?: string;
  detectedDomain?: string;
  uploadedAt: string;
  checksum?: string;
  [key: string]: unknown;
}

export interface ColumnMappingItem {
  canonicalKey: string;
  canonicalLabel?: string;
  canonicalName?: string;
  dataType?: string;
  detectedColumn: string | null;
  confidence: ConfidenceLevel;
  required: boolean;
  sampleValue?: string | number | null;
  status: 'valid' | 'missing' | 'warning';
  [key: string]: unknown;
}

export interface DataInspectionRow {
  [key: string]: string | number | boolean | null | undefined;
}

export interface ValidationIssue {
  id?: string;
  severity: IssueSeverity;
  field?: string;
  message: string;
  remediationSuggestion?: string;
  [key: string]: unknown;
}

export type IntakeStage =
  | 'idle'
  | 'file_received'
  | 'understanding_data'
  | 'mapping_structure'
  | 'validating'
  | 'ready'
  | 'error';

export type PipelineStage =
  | IntakeStage
  | 'uploading'
  | 'parsing'
  | 'transforming'
  | 'completed'
  | 'failed';

export interface IntakeState {
  stage: IntakeStage;
  progressPercent: number;
  metadata: IngestionMetadata | null;
  mappings: ColumnMappingItem[];
  previewRows: DataInspectionRow[];
  validationIssues: ValidationIssue[];
  isSubmitting: boolean;
  errorMessage?: string;
}