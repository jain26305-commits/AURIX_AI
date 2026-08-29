import { AlertFeedReport } from '@/types/alert.types';

export class AlertAdapter {
  public static generateSimulatedAlerts(): AlertFeedReport {
    return {
      evaluatedAt: new Date().toISOString(),
      summary: {
        totalActive: 4,
        criticalCount: 2,
        warningCount: 1,
        infoCount: 1,
        totalFinancialExposureINR: 424300,
        unacknowledgedCount: 3,
      },
      alerts: [
        {
          id: 'ALT-9041',
          title: 'Stockout Projected within 6 Days for SKU-004',
          domain: 'INVENTORY',
          severity: 'CRITICAL',
          status: 'ACTIVE',
          entityId: 'SKU-004',
          entityName: '103 Black-XXL (Hoodie)',
          summary: 'Forward cover dropped to 15 days against a 35-day lead-time requirement during seasonal surge.',
          exposureINR: 112500,
          breachWindow: '6 Days',
          detectedAt: new Date(Date.now() - 1000 * 60 * 45).toISOString(),
          provenance: {
            ruleOrModel: 'Deterministic ROP Policy Solver',
            thresholdTriggered: 'On-Hand <= Safety Stock Buffer (65 units)',
            actualValue: '42 units on hand',
          },
        },
        {
          id: 'ALT-9042',
          title: 'Freight Lane Congestion on Surat-Bengaluru Corridor',
          domain: 'LOGISTICS',
          severity: 'CRITICAL',
          status: 'ACTIVE',
          entityId: 'PO-2025-084',
          entityName: 'Surat Central Fabric Mill Dispatch',
          summary: 'Consignment TRK-90214 delayed by +2.5 days. Delay probability evaluated at 84%.',
          exposureINR: 58200,
          breachWindow: '+2.5 Days Late',
          detectedAt: new Date(Date.now() - 1000 * 60 * 120).toISOString(),
          provenance: {
            ruleOrModel: 'Logistics Lane P90 Variance Monitor',
            thresholdTriggered: 'Carrier Delay Variance > 1.5 days',
            actualValue: '+2.5 days variance',
          },
        },
        {
          id: 'ALT-9043',
          title: 'Processing Mill Bottleneck at Apex Tiruppur Facility',
          domain: 'SUPPLY',
          severity: 'WARNING',
          status: 'ACKNOWLEDGED',
          entityId: 'VEND-001',
          entityName: 'Apex Mills & Fabrics Pvt Ltd',
          summary: 'Capacity utilization hit 94.5%. Turnaround time inflated by +3.8 days on pending batches.',
          exposureINR: 40000,
          breachWindow: '14 Days Window',
          detectedAt: new Date(Date.now() - 1000 * 60 * 240).toISOString(),
          acknowledgedBy: 'Kaushik Jain (Executive)',
          provenance: {
            ruleOrModel: 'Supplier Work-Center Capacity Tracker',
            thresholdTriggered: 'Facility Load >= 90.0%',
            actualValue: '94.5% utilization',
          },
        },
        {
          id: 'ALT-9044',
          title: 'Working Capital Lockup on SKU-005 Slow-Moving Inventory',
          domain: 'INVENTORY',
          severity: 'INFO',
          status: 'ACTIVE',
          entityId: 'SKU-005',
          entityName: '104 Olive-M (Jeans)',
          summary: 'Stock cover stands at 331 days forward horizon, locking ₹2.13L excess working capital.',
          exposureINR: 213600,
          breachWindow: 'Long-term Drag',
          detectedAt: new Date(Date.now() - 1000 * 60 * 600).toISOString(),
          provenance: {
            ruleOrModel: 'Working Capital Rightsizing Engine',
            thresholdTriggered: 'Days of Cover >= 180 Days',
            actualValue: '331 Days Cover',
          },
        },
      ],
    };
  }
}