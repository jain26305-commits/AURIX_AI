export type ParetoTier = 'TIER_A' | 'TIER_B' | 'TIER_C';
export type AccountHealthStatus = 'THRIVING' | 'STABLE' | 'AT_RISK' | 'DORMANT' | 'CHURNED';
export type VelocityTier = 'FAST_MOVING' | 'STEADY' | 'SLOW_MOVING' | 'DEAD_STOCK';

export interface CommercialSummaryDTO {
  tenantId: string;
  periodKey: string;
  grossRevenue: number;
  netRevenue: number;
  totalOrders: number;
  averageOrderValue: number;
  activeCustomersCount: number;
  dormantCustomersCount: number;
  commercialOtifPct: number;
  overallDiscountPct: number;
  topGrowthChannel: string;
  activeAnomaliesCount: number;
  evaluatedAt: string;
}

export interface Account360DTO {
  customerId: string;
  customerName: string;
  segment: string;
  paretoTier: ParetoTier;
  healthStatus: AccountHealthStatus;
  healthScore: number;
  lifetimeRevenue: number;
  periodRevenue: number;
  orderCount: number;
  averageOrderValue: number;
  daysSinceLastOrder: number;
  grossMarginPct: number;
  discountRatePct: number;
  otifRatePct: number;
}

export interface CommercialOTIFDTO {
  tenantId: string;
  periodKey: string;
  totalOrders: number;
  otifOrders: number;
  otifRatePct: number;
  fillRatePct: number;
  averageLeadTimeDays: number;
  backlogOrderCount: number;
  cancellationRatePct: number;
}

export interface PVMDecompositionDTO {
  tenantId: string;
  baselineRevenue: number;
  currentRevenue: number;
  totalRevenueChange: number;
  priceEffect: number;
  volumeEffect: number;
  mixEffect: number;
  priceEffectPct: number;
  volumeEffectPct: number;
  mixEffectPct: number;
}
