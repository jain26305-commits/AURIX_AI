export type AbcClass = 'A' | 'B' | 'C';
export type XyzClass = 'X' | 'Y' | 'Z';
export type DemandPatternType = 'Smooth' | 'Erratic' | 'Intermittent' | 'Lumpy';

export interface MonthlyDataPoint {
  month: string;
  demand: number;
  revenue: number;
}

export interface SkuDemandProfile {
  skuId: string;
  skuName: string;
  category: string;
  abcClass: AbcClass;
  xyzClass: XyzClass;
  demandPattern: DemandPatternType;
  totalVolume: number;
  totalRevenueINR: number;
  meanMonthlyDemand: number;
  coefficientOfVariation: number; // Volatility metric
  zeroDemandMonths: number;
  monthlyHistory: MonthlyDataPoint[];
}

export interface PortfolioSummaryMetrics {
  totalSkus: number;
  totalAnnualVolume: number;
  totalAnnualRevenueINR: number;
  portfolioMeanCV: number;
  intermittentSkuCount: number;
  abcDistribution: { classA: number; classB: number; classC: number };
  xyzDistribution: { classX: number; classY: number; classZ: number };
}

export interface SeasonalityCell {
  month: string;
  quarter: string;
  averageIndex: number; // 1.0 is baseline, > 1.2 is surge
  peakCategory: string;
}

export interface EdaAnalyticsReport {
  evaluatedAt: string;
  summary: PortfolioSummaryMetrics;
  skuProfiles: SkuDemandProfile[];
  seasonality: SeasonalityCell[];
}