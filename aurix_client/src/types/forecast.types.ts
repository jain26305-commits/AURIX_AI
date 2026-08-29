export type ModelFamily = 'XGBoost Ensemble' | 'SARIMAX' | 'Holt-Winters ETS' | 'Croston Intermittent' | 'Prophet' | 'Naive Baseline';
export type ForecastHorizon = '1M' | '3M' | '6M' | '12M';
export type DemandPatternClass = 'SMOOTH' | 'INTERMITTENT' | 'ERRATIC' | 'LUMPY';
export type AbcClassification = 'A' | 'B' | 'C';
export type XyzClassification = 'X' | 'Y' | 'Z';

export interface ForecastTimelinePoint {
  period: string;
  actual?: number | null;
  forecast?: number | null;
  lowerBound?: number | null; // P10 / 80% CI Lower
  upperBound?: number | null; // P90 / 80% CI Upper
  isHistorical: boolean;
}

export interface CompetingModelResult {
  modelName: ModelFamily;
  wapePercent: number;
  rmse: number;
  mae: number;
  bias: number;
  fitPValue: number;
  isChampion: boolean;
  trainingLatencyMs: number;
}

export interface FeatureImportanceItem {
  featureName: string;
  importanceWeight: number; // 0.0 - 1.0
  impactDirection: 'positive' | 'negative' | 'neutral';
}

export interface IntermittencyMetrics {
  averageDemandIntervalAdi: number; // Threshold 1.32
  coefficientOfVariationSquaredCv2: number; // Threshold 0.49
  patternClass: DemandPatternClass;
  syntetosBoylanRecommendedModel: ModelFamily;
  classificationRationale: string;
}

export interface DistributionProfile {
  meanUnits: number;
  medianUnits: number;
  standardDeviation: number;
  skewness: number;
  kurtosis: number;
  interquartileRangeIqr: number;
  outlierObservationsCount: number;
}

export interface DemandImplicationMetrics {
  recommendedSafetyStockUnits: number;
  currentSafetyStockUnits: number;
  safetyStockBufferDeltaUnits: number;
  workingCapitalExposureInr: number;
  stockoutRevenueAtRiskInr: number;
  abcClass: AbcClassification;
  xyzClass: XyzClassification;
}

export interface ChampionModelMetadata {
  skuId: string;
  skuName: string;
  modelFamily: ModelFamily;
  accuracyWape: number;
  confidenceScorePercent: number;
  horizonUnitsTotal: number;
  historicalMonthsTrained: number;
  forecastHorizon: ForecastHorizon;
  rationale: string;
  featureImportance: FeatureImportanceItem[];
  competingModels: CompetingModelResult[];
  intermittency?: IntermittencyMetrics;
  distribution?: DistributionProfile;
  implications?: DemandImplicationMetrics;
}

export interface ForecastAnalyticsPayload {
  evaluatedAt: string;
  metadata: ChampionModelMetadata;
  timeline: ForecastTimelinePoint[];
}
