export type StockHealthStatus = 'OPTIMAL' | 'RISK_OF_STOCKOUT' | 'CRITICAL_BREACH' | 'EXCESS_INVENTORY';

export interface SkuInventoryMetrics {
  skuId: string;
  skuName: string;
  category: string;
  currentStockUnits: number;
  safetyStockUnits: number;
  reorderPointUnits: number;
  economicOrderQty: number;
  averageDailyDemand: number;
  daysOfCoverRemaining: number;
  serviceLevelTargetPercent: number;
  stockoutProbabilityPercent: number;
  stockoutBreachDays: number | null;
  excessStockUnits: number;
  capitalTiedUpINR: number;
  excessCapitalExposureINR: number;
  stockoutRevenueAtRiskINR: number;
  healthStatus: StockHealthStatus;
  leadTimeDaysUsed: number;
  recommendationAction: string;
}

export interface InventoryPolicyRecalculateRequest {
  skuId: string;
  serviceLevelTargetPercent: number;
}

export interface InventoryPolicyRecalculateResponse {
  skuId: string;
  serviceLevelTargetPercent: number;
  computedSafetyStockUnits: number;
  computedReorderPointUnits: number;
  leadTimeDemandUnits: number;
  zScoreUsed: number;
  stockoutProbabilityPercent: number;
  recommendationAction: string;
}

export interface InventoryPortfolioSummary {
  totalInventoryValuationINR: number;
  totalWorkingCapitalExcessINR: number;
  totalStockoutExposureINR: number;
  portfolioServiceLevelPercent: number;
  skusAtStockoutRiskCount: number;
  skusWithExcessStockCount: number;
  skusOptimalCount: number;
}

export interface InventoryAnalyticsReport {
  evaluatedAt: string;
  summary: InventoryPortfolioSummary;
  skuInventories: SkuInventoryMetrics[];
}