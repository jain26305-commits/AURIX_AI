export type ProcessType =
  | 'ORDER_TO_CASH'
  | 'PROCURE_TO_PAY'
  | 'MANUFACTURING_PRODUCTION'
  | 'RETURNS_AND_REVERSE_LOGISTICS';

export interface ProcessSummaryDTO {
  tenantId: string;
  periodKey: string;
  overallProcessHealthScore: number;
  totalEventsProcessed: number;
  activeCasesCount: number;
  discoveredVariantsCount: number;
  conformanceRatePct: number;
  slaComplianceRatePct: number;
  averageO2cCycleDays: number;
  averageP2pCycleDays: number;
  topBottleneckStep: string;
  totalProcessFinancialDragUsd: number;
  evaluatedAt: string;
}

export interface ProcessVariantDTO {
  variantId: string;
  processType: ProcessType;
  stepSequence: string[];
  caseCount: number;
  frequencyPct: number;
  averageDurationHours: number;
  isStandardPath: boolean;
}

export interface ProcessBottleneckDTO {
  bottleneckId: string;
  processType: ProcessType;
  stepName: string;
  queueDepthCases: number;
  averageWaitingHours: number;
  slaBreachRatePct: number;
  severity: string;
  primaryFrictionCause: string;
  annualizedFinancialDrag: number;
}
