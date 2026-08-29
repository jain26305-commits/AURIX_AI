export type CommercialPeriod = 'MTD' | 'QTD' | 'YTD' | 'CUSTOM';

export interface SalesSummaryDTO {
  grossRevenueINR: number;
  netRevenueINR: number;
  revenueGrowthPercent: number;
  revenueVsPlanPercent: number;
  totalOrdersCount: number;
  unitsSold: number;
  averageSellingPriceINR: number;
  grossMarginPercent: number;
  contributionMarginPercent: number;
  activeCustomersCount: number;
  newCustomersCount: number;
  churnedCustomersCount: number;
  revenueAtRiskINR: number;
  lostSalesValueINR: number;
  totalOpportunityValueINR: number;
  evaluatedAt: string;
}

export interface PvmVarianceItem {
  dimension: string;
  baselineRevenueINR: number;
  currentRevenueINR: number;
  netVarianceINR: number;
  priceEffectINR: number;
  volumeEffectINR: number;
  mixEffectINR: number;
  contributionPercent: number;
}

export interface CustomerAccount360 {
  customerId: string;
  customerName: string;
  tier: string;
  segment: string;
  revenueINR: number;
  marginPercent: number;
  ordersCount: number;
  unitsPurchased: number;
  growthPercent: number;
  recencyDays: number;
  retentionRiskScore: number;
  creditLimitINR: number;
  outstandingBalanceINR: number;
  overdueDaysMax: number;
  segmentRisk: 'LOW' | 'MODERATE' | 'CRITICAL';
}

export interface CustomerConcentrationItem {
  tierName: string;
  customerCount: number;
  revenueINR: number;
  revenueSharePercent: number;
  cumulativeSharePercent: number;
  hhiContribution: number;
}

export interface OrderToCashRiskItem {
  invoiceId: string;
  customerId: string;
  customerName: string;
  invoiceAmountINR: number;
  dueDate: string;
  daysSalesOutstanding: number;
  overdueDays: number;
  riskStatus: 'CURRENT' | 'WATCHLIST' | 'OVERDUE_CRITICAL' | 'BLOCKED';
}

export interface CommercialOpportunityItem {
  opportunityId: string;
  customerId: string;
  customerName: string;
  opportunityType: 'UPSELL' | 'CROSS_SELL' | 'PRICE_OPTIMIZATION' | 'WIN_BACK';
  description: string;
  estimatedValueINR: number;
  confidenceScore: number;
  suggestedAction: string;
}

export interface SalesAnalyticsReport {
  evaluatedAt: string;
  summary: SalesSummaryDTO;
  pvmBreakdown: PvmVarianceItem[];
  customers: CustomerAccount360[];
  concentration: CustomerConcentrationItem[];
  o2cRisks: OrderToCashRiskItem[];
  opportunities: CommercialOpportunityItem[];
}
