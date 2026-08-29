export type SignalSeverity = 'CRITICAL' | 'HIGH' | 'WATCH' | 'OPPORTUNITY';
export type WorkflowStatus = 'PENDING_REVIEW' | 'APPROVED' | 'REJECTED' | 'ASSIGNED' | 'EXECUTED';
export type ActionCategory = 
  | 'EXPEDITE_SHIPMENT'
  | 'REORDER_INVENTORY'
  | 'SAFETY_STOCK_BUFFER'
  | 'SUPPLIER_SWAP'
  | 'PRICE_MARKDOWN'
  | 'CAPACITY_REBALANCE';

export interface RecommendationProvenance {
  dataSource: string;
  modelUsed: string;
  datasetChecksum: string;
  assumptions: string[];
  evaluatedTimestamp: string;
  dataQualityPassRate: number;
}

export interface RecommendationItem {
  id: string;
  title: string;
  targetSkuId?: string;
  targetSkuName?: string;
  category: ActionCategory;
  severity: SignalSeverity;
  status: WorkflowStatus;
  confidencePercent: number;
  dataQualityScore: number;
  whatHappened: string;
  rootCause: string;
  prescriptiveAction: string;
  costToExecuteINR: number;
  financialImpactAvoidedINR: number;
  costOfInactionINR: number;
  expectedServiceLevelRestoredPercent: number;
  provenance: RecommendationProvenance;
  assignedTo?: string;
  actionLoggedAt?: string;
}

export interface RecommendationSummaryMetrics {
  totalSignalsActive: number;
  criticalActionCount: number;
  totalExposureAvoidableINR: number;
  totalExecutionCapitalRequiredINR: number;
  pendingApprovalsCount: number;
}

export interface RecommendationFeedReport {
  evaluatedAt: string;
  summary: RecommendationSummaryMetrics;
  recommendations: RecommendationItem[];
}