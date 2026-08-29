export type ActionLifecycleState =
  | 'PENDING'
  | 'PREFLIGHT'
  | 'AWAITING_APPROVAL'
  | 'APPROVED'
  | 'EXECUTING'
  | 'EXECUTED'
  | 'FAILED'
  | 'RECONCILED';

export type ActionPriority = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
export type ActionDomain = 'INVENTORY' | 'LOGISTICS' | 'PROCUREMENT' | 'PRICING' | 'MANUFACTURING';

export interface PreflightValidationCheck {
  checkId: string;
  name: string;
  category: 'SECURITY_RBAC' | 'BUDGET_CAPITAL' | 'ERP_CONNECTIVITY' | 'BUSINESS_CONSTRAINT';
  passed: boolean;
  message: string;
  timestamp: string;
}

export interface CryptographicExecutionToken {
  tokenId: string;
  signedBy: string;
  role: string;
  timestamp: string;
  sha256Checksum: string;
  phase14AuthorizationCode: string;
}

export interface Phase14ActionItem {
  id: string;
  title: string;
  domain: ActionDomain;
  priority: ActionPriority;
  state: ActionLifecycleState;
  targetEntityId: string;
  targetEntityName: string;
  prescriptivePayload: {
    actionType: string;
    quantity?: number;
    destination?: string;
    carrier?: string;
    financialCommitmentINR: number;
    expectedRoiINR: number;
  };
  initiatedBy: string;
  assignedApproverRole: string;
  createdAt: string;
  updatedAt: string;
  preflightChecks: PreflightValidationCheck[];
  preflightCleared: boolean;
  executionToken?: CryptographicExecutionToken;
  errorMessage?: string;
  auditTrail: {
    timestamp: string;
    state: ActionLifecycleState;
    actor: string;
    note: string;
  }[];
}

export interface ActionCenterSummary {
  totalPendingCount: number;
  awaitingApprovalCount: number;
  executingCount: number;
  executedTodayCount: number;
  failedCount: number;
  totalCommittedCapitalINR: number;
  totalProtectedExposureINR: number;
}

export interface ActionCenterFeedReport {
  evaluatedAt: string;
  summary: ActionCenterSummary;
  actions: Phase14ActionItem[];
}