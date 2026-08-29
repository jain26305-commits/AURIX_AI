export type SupplierRiskLevel = 'LOW' | 'MODERATE' | 'ELEVATED' | 'HIGH';

export interface LeadTimeDistribution {
  meanDays: number;
  medianDays: number;
  p75Days: number;
  p90Days: number;
  p95Days: number;
  standardDeviationDays: number;
  sampleDeliveriesCount: number;
  frequencyBins: { daysRange: string; frequencyPercent: number }[];
}

export interface SupplierPerformanceProfile {
  supplierId: string;
  supplierName: string;
  primaryCategory: string;
  reliabilityScorePercent: number;
  onTimeInFullPercent: number; // OTIF
  fillRatePercent: number;
  orderDelayProbabilityPercent: number;
  riskLevel: SupplierRiskLevel;
  totalOrdersFulfilled: number;
  activePurchaseOrders: number;
  leadTime: LeadTimeDistribution;
  qualityDefectPpm: number;
  paymentTerms: string;
  recommendationNotes: string;
}

export interface SupplyPortfolioSummary {
  activeSupplierCount: number;
  portfolioMeanOTIFPercent: number;
  portfolioMeanLeadTimeDays: number;
  highRiskSupplierCount: number;
  pendingInboundUnits: number;
}

export interface SupplierCandidate {
  supplierId: string;
  supplierName: string;
  matchScorePercent: number;
  estimatedLeadTimeDays: number;
  unitCostINR: number;
  qualificationStatus: 'QUALIFIED' | 'PENDING_AUDIT' | 'UNQUALIFIED';
}

export interface DualSourcingRecommendation {
  targetSkuId: string;
  targetSkuCategory: string;
  currentPrimarySupplierId: string;
  annualizedSpendExposureINR: number;
  recommendedCandidates: SupplierCandidate[];
}

export interface SupplyAnalyticsReport {
  evaluatedAt: string;
  summary: SupplyPortfolioSummary;
  suppliers: SupplierPerformanceProfile[];
  dualSourcingRecommendations?: DualSourcingRecommendation[];
}
