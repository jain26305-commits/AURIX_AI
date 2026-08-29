export interface RiskFindingDTO {
  riskId?: string;
  tenantId?: string;
  riskDomain?: string;
  entityType?: string;
  entityId?: string;
  title?: string;
  description?: string;
  probability?: number;
  impactAmountUsd?: number;
  exposureAmountUsd?: number;
  confidenceLevel?: number;
  severity?: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' | string;
  status?: string;
  firstDetected?: string;
  [key: string]: any;
}

export interface OpportunityFindingDTO {
  opportunityId?: string;
  tenantId?: string;
  title?: string;
  valueUsd?: number;
  [key: string]: any;
}

export interface RiskSummaryDTO {
  overallRiskScore?: number;
  totalActiveFindings?: number;
  totalFinancialExposureUsd?: number;
  criticalRisksCount?: number;
  findings?: RiskFindingDTO[];
  totalActiveRisksCount?: number;
  totalExposureUsd?: number;
  totalExpectedLossUsd?: number;
  criticalPrioritiesCount?: number;
  topRiskDomain?: string;
  activeOpportunitiesCount?: number;
  totalOpportunityValueUsd?: number;
  activeExternalSignalsCount?: number;
  overallRiskCoveragePct?: number;
  evaluatedAt?: string;
  [key: string]: any;
}
