export type ReadinessState = 'READY' | 'PARTIAL' | 'BLOCKED';
export type QualitySeverity = 'critical' | 'warning' | 'info';

export interface QualityDimensionScore {
  key: string;
  name: string;
  score: number; // 0 - 100
  status: 'optimal' | 'acceptable' | 'deficient';
  description: string;
  affectedRecords: number;
  totalRecords: number;
}

export interface ModuleReadinessItem {
  moduleKey: 'forecasting' | 'inventory' | 'supply' | 'lead_time' | 'logistics' | 'finance' | 'network';
  moduleName: string;
  state: ReadinessState;
  score: number;
  unmetPrerequisites: string[];
  clearanceNote: string;
}

export interface DataAnomalyItem {
  id: string;
  skuId?: string;
  field: string;
  rowNumber?: number;
  severity: QualitySeverity;
  category: 'missing_value' | 'outlier' | 'duplicate' | 'temporal_gap' | 'type_mismatch' | 'negative_value';
  valueDetected: string | number | null;
  expectedCondition: string;
  remediationAction: string;
}

export interface QualityAuditReport {
  overallScore: number;
  overallHealth: 'OPTIMAL' | 'ACCEPTABLE' | 'DEGRADED';
  totalRowsAudited: number;
  totalColumnsAudited: number;
  temporalRange: { start: string; end: string };
  evaluatedAt: string;
  dimensions: QualityDimensionScore[];
  readinessMatrix: ModuleReadinessItem[];
  anomalies: DataAnomalyItem[];
}