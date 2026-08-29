import { SupplyAnalyticsReport, SupplierPerformanceProfile, DualSourcingRecommendation } from '@/types/supply.types';

export class SupplyAdapter {
  public static generateSimulatedSupply(): SupplyAnalyticsReport {
    const suppliers: SupplierPerformanceProfile[] = [
      {
        supplierId: 'VEND-001',
        supplierName: 'Apex Mills & Fabrics Pvt Ltd',
        primaryCategory: 'T-Shirts & Polos',
        reliabilityScorePercent: 94.2,
        onTimeInFullPercent: 92.8,
        fillRatePercent: 97.4,
        orderDelayProbabilityPercent: 7.2,
        riskLevel: 'LOW',
        totalOrdersFulfilled: 148,
        activePurchaseOrders: 3,
        leadTime: {
          meanDays: 24.2,
          medianDays: 23.0,
          p75Days: 27.0,
          p90Days: 31.0,
          p95Days: 34.0,
          standardDeviationDays: 3.8,
          sampleDeliveriesCount: 148,
          frequencyBins: [
            { daysRange: '15-20d', frequencyPercent: 18 },
            { daysRange: '21-25d', frequencyPercent: 54 },
            { daysRange: '26-30d', frequencyPercent: 20 },
            { daysRange: '31-35d', frequencyPercent: 6 },
            { daysRange: '35d+', frequencyPercent: 2 },
          ],
        },
        qualityDefectPpm: 240,
        paymentTerms: 'Net 45 Days',
        recommendationNotes: 'Prime tier vendor. Highly predictable turnaround; suitable for high-volume Class A lines.',
      },
      {
        supplierId: 'VEND-002',
        supplierName: 'Vanguard Knits & Fleece Ltd',
        primaryCategory: 'Hoodies & Sweatshirts',
        reliabilityScorePercent: 76.5,
        onTimeInFullPercent: 71.0,
        fillRatePercent: 88.2,
        orderDelayProbabilityPercent: 29.0,
        riskLevel: 'ELEVATED',
        totalOrdersFulfilled: 64,
        activePurchaseOrders: 2,
        leadTime: {
          meanDays: 38.6,
          medianDays: 35.0,
          p75Days: 44.0,
          p90Days: 52.0,
          p95Days: 58.0,
          standardDeviationDays: 8.4,
          sampleDeliveriesCount: 64,
          frequencyBins: [
            { daysRange: '20-30d', frequencyPercent: 12 },
            { daysRange: '31-40d', frequencyPercent: 46 },
            { daysRange: '41-50d', frequencyPercent: 28 },
            { daysRange: '51-60d', frequencyPercent: 11 },
            { daysRange: '60d+', frequencyPercent: 3 },
          ],
        },
        qualityDefectPpm: 1250,
        paymentTerms: 'Net 30 Days',
        recommendationNotes: 'Significant lead-time tail risk (P95 = 58 days). Require 14-day safety buffer on winter POs.',
      },
      {
        supplierId: 'VEND-003',
        supplierName: 'DenimCraft Apparel Solutions',
        primaryCategory: 'Jeans & Bottoms',
        reliabilityScorePercent: 88.0,
        onTimeInFullPercent: 86.5,
        fillRatePercent: 94.0,
        orderDelayProbabilityPercent: 13.5,
        riskLevel: 'LOW',
        totalOrdersFulfilled: 92,
        activePurchaseOrders: 1,
        leadTime: {
          meanDays: 42.0,
          medianDays: 40.0,
          p75Days: 46.0,
          p90Days: 49.0,
          p95Days: 53.0,
          standardDeviationDays: 4.6,
          sampleDeliveriesCount: 92,
          frequencyBins: [
            { daysRange: '30-38d', frequencyPercent: 15 },
            { daysRange: '39-45d', frequencyPercent: 62 },
            { daysRange: '46-52d', frequencyPercent: 18 },
            { daysRange: '53d+', frequencyPercent: 5 },
          ],
        },
        qualityDefectPpm: 480,
        paymentTerms: 'Net 60 Days',
        recommendationNotes: 'Stable long-cycle supplier. Consistent performance across standard 45-day fabrication batches.',
      },
    ];

    const dualSourcingRecommendations: DualSourcingRecommendation[] = [
      {
        targetSkuId: 'SKU-004 (Hoodies)',
        targetSkuCategory: 'Fleece & Knits',
        currentPrimarySupplierId: 'VEND-002',
        annualizedSpendExposureINR: 3750000,
        recommendedCandidates: [
          {
            supplierId: 'CAND-901',
            supplierName: 'Sterling Weaves Industrial Ltd',
            matchScorePercent: 91.5,
            estimatedLeadTimeDays: 28,
            unitCostINR: 880,
            qualificationStatus: 'QUALIFIED',
          },
          {
            supplierId: 'CAND-902',
            supplierName: 'Orient Fleece Works',
            matchScorePercent: 84.0,
            estimatedLeadTimeDays: 32,
            unitCostINR: 840,
            qualificationStatus: 'PENDING_AUDIT',
          },
        ],
      },
    ];

    return {
      evaluatedAt: new Date().toISOString(),
      summary: {
        activeSupplierCount: 3,
        portfolioMeanOTIFPercent: 83.4,
        portfolioMeanLeadTimeDays: 34.9,
        highRiskSupplierCount: 1,
        pendingInboundUnits: 850,
      },
      suppliers,
      dualSourcingRecommendations,
    };
  }
}
