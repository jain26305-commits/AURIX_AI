export type CaseStage =
  | 'OPEN'
  | 'INVESTIGATING'
  | 'AWAITING_DECISION'
  | 'AWAITING_APPROVAL'
  | 'RESOLVED'
  | 'CLOSED'
  | 'ESCALATED';

export type CasePriority = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';

export interface CaseProvenanceStep {
  stepIndex: number;
  stage: string;
  title: string;
  actorOrSystem: string;
  timestamp: string;
  summary: string;
  artifacts?: { key: string; value: string }[];
}

export interface OperationalCase {
  id: string;
  title: string;
  domain: string;
  priority: CasePriority;
  stage: CaseStage;
  owner: string;
  targetEntityId: string;
  targetEntityName: string;
  alertId?: string;
  summary: string;
  rootCauseAttribution: string;
  exposureINR: number;
  serviceImpactPercent: number;
  createdAt: string;
  updatedAt: string;
  resolvedAt?: string;
  provenanceLineage: CaseProvenanceStep[];
}

export interface CaseSummaryMetrics {
  totalOpenCases: number;
  investigatingCount: number;
  awaitingApprovalCount: number;
  resolvedCount: number;
  criticalPriorityCount: number;
  aggregateExposureAtStakeINR: number;
}

export interface CaseManagementReport {
  evaluatedAt: string;
  summary: CaseSummaryMetrics;
  cases: OperationalCase[];
}