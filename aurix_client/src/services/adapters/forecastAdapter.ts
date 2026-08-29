import { ForecastAnalyticsPayload, ForecastHorizon } from '@/types/forecast.types';

export class ForecastAdapter {
  public static generateSimulatedForecast(skuId: string = 'SKU-001', horizon: ForecastHorizon = '3M'): ForecastAnalyticsPayload {
    const historicalPeriods = [
      { period: 'May 2024', actual: 130, isHistorical: true },
      { period: 'Jun 2024', actual: 145, isHistorical: true },
      { period: 'Jul 2024', actual: 138, isHistorical: true },
      { period: 'Aug 2024', actual: 120, isHistorical: true },
      { period: 'Sep 2024', actual: 115, isHistorical: true },
      { period: 'Oct 2024', actual: 132, isHistorical: true },
      { period: 'Nov 2024', actual: 102, isHistorical: true },
      { period: 'Dec 2024', actual: 105, isHistorical: true },
      { period: 'Jan 2025', actual: 112, isHistorical: true },
    ];

    // Forecast horizons
    const projectionPeriods = [
      { period: 'Feb 2025', forecast: 118, lowerBound: 104, upperBound: 132, isHistorical: false },
      { period: 'Mar 2025', forecast: 126, lowerBound: 108, upperBound: 144, isHistorical: false },
      { period: 'Apr 2025', forecast: 134, lowerBound: 112, upperBound: 156, isHistorical: false },
      { period: 'May 2025', forecast: 142, lowerBound: 118, upperBound: 168, isHistorical: false },
      { period: 'Jun 2025', forecast: 150, lowerBound: 122, upperBound: 178, isHistorical: false },
      { period: 'Jul 2025', forecast: 140, lowerBound: 110, upperBound: 170, isHistorical: false },
    ];

    const sliceCount = horizon === '1M' ? 1 : horizon === '3M' ? 3 : horizon === '6M' ? 6 : 6;
    const activeProjections = projectionPeriods.slice(0, sliceCount);

    const timeline = [
      ...historicalPeriods.map((h) => ({
        period: h.period,
        actual: h.actual,
        forecast: null,
        lowerBound: null,
        upperBound: null,
        isHistorical: true,
      })),
      ...activeProjections.map((p) => ({
        period: p.period,
        actual: null,
        forecast: p.forecast,
        lowerBound: p.lowerBound,
        upperBound: p.upperBound,
        isHistorical: false,
      })),
    ];

    return {
      evaluatedAt: new Date().toISOString(),
      metadata: {
        skuId,
        skuName: skuId === 'SKU-001' ? '101 Beige-L (T-Shirt)' : '101 Beige-M (T-Shirt)',
        modelFamily: 'XGBoost Ensemble',
        accuracyWape: 8.2, // 91.8% accuracy
        confidenceScorePercent: 93.4,
        horizonUnitsTotal: activeProjections.reduce((acc, curr) => acc + curr.forecast, 0),
        historicalMonthsTrained: 18,
        forecastHorizon: horizon,
        rationale:
          'XGBoost Ensemble outperformed SARIMAX and Holt-Winters by 3.4% on out-of-sample backtesting, capturing non-linear promotion spikes and seasonal summer surges without residual bias.',
        featureImportance: [
          { featureName: '12-Month Seasonal Lag (t-12)', importanceWeight: 0.38, impactDirection: 'positive' },
          { featureName: 'Prior 3-Month Moving Average', importanceWeight: 0.26, impactDirection: 'positive' },
          { featureName: 'Promotional Campaign Flag', importanceWeight: 0.18, impactDirection: 'positive' },
          { featureName: 'Category Demand Velocity', importanceWeight: 0.12, impactDirection: 'neutral' },
          { featureName: 'Price Elasticity Coefficient', importanceWeight: 0.06, impactDirection: 'negative' },
        ],
        competingModels: [
          {
            modelName: 'XGBoost Ensemble',
            wapePercent: 8.2,
            rmse: 11.4,
            mae: 9.6,
            bias: -0.4,
            fitPValue: 0.89,
            isChampion: true,
            trainingLatencyMs: 142,
          },
          {
            modelName: 'SARIMAX',
            wapePercent: 11.6,
            rmse: 15.2,
            mae: 13.8,
            bias: 2.1,
            fitPValue: 0.74,
            isChampion: false,
            trainingLatencyMs: 86,
          },
          {
            modelName: 'Holt-Winters ETS',
            wapePercent: 13.8,
            rmse: 18.0,
            mae: 16.2,
            bias: -3.8,
            fitPValue: 0.62,
            isChampion: false,
            trainingLatencyMs: 34,
          },
          {
            modelName: 'Prophet',
            wapePercent: 14.5,
            rmse: 19.8,
            mae: 17.1,
            bias: 4.2,
            fitPValue: 0.58,
            isChampion: false,
            trainingLatencyMs: 310,
          },
          {
            modelName: 'Naive Baseline',
            wapePercent: 24.1,
            rmse: 32.6,
            mae: 28.5,
            bias: -8.6,
            fitPValue: 0.12,
            isChampion: false,
            trainingLatencyMs: 4,
          },
        ],
      },
      timeline,
    };
  }
}