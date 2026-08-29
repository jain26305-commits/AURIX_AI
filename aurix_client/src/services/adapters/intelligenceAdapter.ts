import { RecommendationFeedReport, RecommendationItem } from '@/types/recommendation.types';

export class IntelligenceAdapter {
  public static generateSimulatedRecommendations(): RecommendationFeedReport {
    const recommendations: RecommendationItem[] = [
      {
        id: 'REC-2025-01',
        title: 'Projected Service Level Breach for SKU-004 (Hoodies)',
        targetSkuId: 'SKU-004',
        targetSkuName: '103 Black-XXL (Hoodie)',
        category: 'EXPEDITE_SHIPMENT',
        severity: 'CRITICAL',
        status: 'PENDING_REVIEW',
        confidencePercent: 94.5,
        dataQualityScore: 96.0,
        whatHappened: 'SKU-004 inventory is projected to reach stockout state in 6 days due to an early seasonal demand spike (140 units forecast vs 42 units on-hand).',
        rootCause: 'Inbound PO-2025-084 delayed by 2.5 days from Surat Mill combined with high historical lead-time tail variance (P95 = 58 days).',
        prescriptiveAction: 'Expedite 300 units from secondary regional hub via Air Freight corridor. Authorize dispatch immediately.',
        costToExecuteINR: 42000,
        financialImpactAvoidedINR: 158700,
        costOfInactionINR: 112500,
        expectedServiceLevelRestoredPercent: 98.4,
        provenance: {
          dataSource: 'Enterprise ERP + Telemetry Lane Feed',
          modelUsed: 'XGBoost ML Forecaster + Deterministic ROP Solver',
          datasetChecksum: 'sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
          assumptions: [
            'Daily demand surge modeled at +20% over 30-day window',
            'Air cargo turnaround verified at 24 hours from Bengaluru hub',
            'Gross margin per unit: ₹529',
          ],
          evaluatedTimestamp: new Date().toISOString(),
          dataQualityPassRate: 96.0,
        },
      },
      {
        id: 'REC-2025-02',
        title: 'Capital Lockup & Slow-Moving Excess on SKU-005 (Jeans)',
        targetSkuId: 'SKU-005',
        targetSkuName: '104 Olive-M (Jeans)',
        category: 'PRICE_MARKDOWN',
        severity: 'HIGH',
        status: 'PENDING_REVIEW',
        confidencePercent: 91.0,
        dataQualityScore: 94.2,
        whatHappened: 'SKU-005 holds 331 days of forward stock cover (285 units on-hand vs 0.86 daily demand), exceeding safe 90-day threshold.',
        rootCause: 'Batch over-ordering in Q3 combined with demand velocity deceleration post-festive season.',
        prescriptiveAction: 'Initiate a 15% targeted promotional campaign across digital storefronts and freeze replenishment POs for 90 days.',
        costToExecuteINR: 18500,
        financialImpactAvoidedINR: 213600,
        costOfInactionINR: 47000, // 22% annual carrying drag
        expectedServiceLevelRestoredPercent: 90.0,
        provenance: {
          dataSource: 'WMS Closing Balances + POS Sales Ledger',
          modelUsed: 'Working Capital Rightsizing Engine',
          datasetChecksum: 'sha256:9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
          assumptions: [
            'Price elasticity coefficient: -1.45',
            'Target stock reduction: 178 units in 45 days',
            'Holding rate carrying cost: 22% per annum',
          ],
          evaluatedTimestamp: new Date().toISOString(),
          dataQualityPassRate: 94.2,
        },
      },
      {
        id: 'REC-2025-03',
        title: 'Supplier Capacity Bottleneck at Tier-1 Tiruppur Processing Mill',
        targetSkuId: 'SKU-001',
        targetSkuName: '101 Beige-L (T-Shirt)',
        category: 'CAPACITY_REBALANCE',
        severity: 'WATCH',
        status: 'PENDING_REVIEW',
        confidencePercent: 88.0,
        dataQualityScore: 92.5,
        whatHappened: 'Apex Mill capacity utilization reached 94.5%, increasing order-to-dispatch turnaround by 3.8 days.',
        rootCause: 'Consolidation of multi-client dyeing batches causing order queuing at finishing stage.',
        prescriptiveAction: 'Split upcoming Q2 PO-2025-095: allocate 60% to Apex Mill and 40% to pre-qualified secondary vendor VEND-003.',
        costToExecuteINR: 12000,
        financialImpactAvoidedINR: 84000,
        costOfInactionINR: 65000,
        expectedServiceLevelRestoredPercent: 96.5,
        provenance: {
          dataSource: 'Vendor EDI Portal + Lane Milestone Telemetry',
          modelUsed: 'Multi-Echelon Network Flow Solver',
          datasetChecksum: 'sha256:4b227777d4dd1fc61c6f884f48641d02b4d121d3fd328cb08b5531fcacdabf8a',
          assumptions: [
            'Secondary vendor unit cost premium: +₹8 per piece',
            'Lead time compressed from 28d to 18d for split batch',
          ],
          evaluatedTimestamp: new Date().toISOString(),
          dataQualityPassRate: 92.5,
        },
      },
    ];

    const totalAvoidable = recommendations.reduce((acc, r) => acc + r.financialImpactAvoidedINR, 0);
    const totalCost = recommendations.reduce((acc, r) => acc + r.costToExecuteINR, 0);

    return {
      evaluatedAt: new Date().toISOString(),
      summary: {
        totalSignalsActive: recommendations.length,
        criticalActionCount: recommendations.filter((r) => r.severity === 'CRITICAL').length,
        totalExposureAvoidableINR: totalAvoidable,
        totalExecutionCapitalRequiredINR: totalCost,
        pendingApprovalsCount: recommendations.filter((r) => r.status === 'PENDING_REVIEW').length,
      },
      recommendations,
    };
  }
}