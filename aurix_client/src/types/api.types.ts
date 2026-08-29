export type ApiMode = 'MOCK' | 'PRODUCTION';

export interface ApiErrorDetails {
  code: string;
  message: string;
  statusCode: number;
  details?: unknown;
  timestamp: string;
}

export class ApiError extends Error {
  public code: string;
  public statusCode: number;
  public details?: unknown;
  public timestamp: string;

  constructor(error: ApiErrorDetails) {
    super(error.message);
    this.name = 'ApiError';
    this.code = error.code;
    this.statusCode = error.statusCode;
    this.details = error.details;
    this.timestamp = error.timestamp;
  }
}

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  timestamp: string;
  executionTimeMs?: number;
  error?: ApiErrorDetails;
}

export interface ApiClientConfig {
  baseUrl: string;
  mode: ApiMode;
  timeoutMs: number;
  tenantId: string;
  authToken?: string | null;
}

// --- PHASE 31-B FOUNDATION CONTRACTS ---

export interface ProvenanceMetadata {
  sourceAuthority: string;
  sourceConnector: string;
  calculationModel: string;
  auditHash: string;
  executionTimestamp: string;
  rlsPolicyApplied: string;
}

export interface BusinessInsight {
  id: string;
  title: string;
  type: 'OBSERVATION' | 'CAUSE' | 'INTERPRETATION' | 'IMPLICATION' | 'RECOMMENDATION' | 'RISK' | 'OPPORTUNITY';
  severity: 'INFO' | 'WARNING' | 'CRITICAL';
  description: string;
  quantitativeImpact?: string;
  financialImpactValue?: number;
  evidenceDataIds?: string[];
}

export interface ScenarioContext {
  scenarioId: string;
  baselineId: string;
  name: string;
  isActive: boolean;
}

export interface ActionPreflightResult {
  status: 'PASSED' | 'PENDING' | 'REJECTED';
  checks: {
    name: string;
    passed: boolean;
    message?: string;
  }[];
}
