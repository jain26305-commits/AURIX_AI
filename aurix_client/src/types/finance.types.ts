// Preserved Phase 8 supply chain economics types
export interface WorkingCapitalWaterfallItem {
  category: string;
  amountINR: number;
  type: 'base' | 'negative' | 'positive' | 'total';
  description: string;
}

export interface WorkingCapitalBreakdown {
  grossInventoryValuationINR: number;
  healthyCycleStockINR: number;
  safetyBufferCapitalINR: number;
  slowMovingCapitalINR: number;
  excessDeadStockINR: number;
  annualHoldingCostINR: number;
  stockoutRevenueLostINR: number;
  expeditedFreightPremiumINR: number;
  unlockedCapitalOpportunityINR: number;
}

export interface FinancialExposureReport {
  evaluatedAt: string;
  holdingRateAnnualPercent: number;
  metrics: WorkingCapitalBreakdown;
  waterfallBridge: WorkingCapitalWaterfallItem[];
}

// Phase 21 & 31-B.10 Business Finance Intelligence Types
export type DataAvailabilityStatus = 'AVAILABLE' | 'PARTIALLY_AVAILABLE' | 'UNAVAILABLE';

export interface FinanceSummaryDTO {
  tenantId: string;
  reportingCurrency: string;
  fiscalPeriod: string;
  grossRevenue: number;
  netRevenue: number;
  cogs: number;
  grossProfit: number;
  grossMarginPercent: number;
  operatingWorkingCapital: number;
  cashConversionCycleDays: number;
  daysSalesOutstanding: number;
  daysPayablesOutstanding: number;
  daysInventoryOutstanding: number;
  activeAnomaliesCount: number;
  totalReceivablesOverdue: number;
  evaluatedAt: string;
}

export interface PnLStatementDTO {
  tenantId: string;
  periodKey: string;
  grossRevenue: number;
  returns: number;
  discounts: number;
  credits: number;
  netRevenue: number;
  cogs: number;
  grossProfit: number;
  grossMarginPercent: number;
  operatingExpenses: number | null;
  operatingProfit: number | null;
  operatingProfitStatus: DataAvailabilityStatus;
  ebitda: number | null;
  ebitdaStatus: DataAvailabilityStatus;
}

export interface ARAgingBucketDTO {
  bucket: 'CURRENT' | '1_30' | '31_60' | '61_90' | '90_PLUS';
  label: string;
  totalAmount: number;
  invoicesCount: number;
  percentOfTotal: number;
}

export interface ARAgingReportDTO {
  tenantId: string;
  totalReceivables: number;
  totalOverdue: number;
  dsoDays: number;
  buckets: ARAgingBucketDTO[];
  topOverdueCustomers: Array<{
    customerId: string;
    customerName: string;
    overdueAmount: number;
    oldestInvoiceDays: number;
    riskTier: string;
  }>;
}

export interface APAgingReportDTO {
  tenantId: string;
  totalPayables: number;
  totalOverdue: number;
  dpoDays: number;
  buckets: Array<{
    bucket: 'CURRENT' | '1_30' | '31_60' | '61_90' | '90_PLUS';
    label: string;
    totalAmount: number;
    invoicesCount: number;
  }>;
  upcomingDisbursements: Array<{
    supplierId: string;
    supplierName: string;
    amount: number;
    dueDate: string;
    discountAvailable: boolean;
  }>;
}

export interface WorkingCapitalDTO {
  tenantId: string;
  inventoryValuation: number;
  accountsReceivable: number;
  accountsPayable: number;
  operatingWorkingCapital: number;
  dsoDays: number;
  dioDays: number;
  dpoDays: number;
  cashConversionCycleDays: number;
  drivers: Array<{
    driver: string;
    impactDays: number;
    capitalImpact: number;
    direction: 'FAVORABLE' | 'UNFAVORABLE';
  }>;
}

export interface FinancialAnomalyDTO {
  anomalyId: string;
  domain: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  title: string;
  description: string;
  detectedDeviationPercent: number;
  impactAmount: number;
  entityId: string;
  detectedAt: string;
}
