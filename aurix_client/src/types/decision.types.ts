export interface DecisionOption {
  optionId?: string;
  name?: string;
  expectedValueUsd?: number;
  riskTier?: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' | string;
  leadTimeDays?: number;
  [key: string]: any;
}

export interface DecisionSummaryDTO {
  totalDecisions?: number;
  pendingApprovalsCount?: number;
  potentialRealizedValueUsd?: number;
  autoApprovalRatePct?: number;
  [key: string]: any;
}

export interface UniversalDecisionCardDTO {
  decisionId?: string;
  tenantId?: string;
  domain?: string;
  decisionDomain?: string;
  decisionType?: string;
  entityType?: string;
  entityId?: string;
  title?: string;
  whySummary?: string;
  whyContext?: string;
  recommendedAction?: string;
  decisionState?: string;
  options?: DecisionOption[];
  confidenceLevel?: number;
  expectedValueUsd?: number;
  createdAt?: string;
  [key: string]: any;
}

export interface DecisionCandidate extends UniversalDecisionCardDTO {}
