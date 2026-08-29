import { NetworkAnalyticsReport } from '@/types/network.types';
import { ApiClient } from '@/services/api/apiClient';

export class NetworkAdapter {
  public static generateSimulatedNetwork(): NetworkAnalyticsReport {
    const isMock = ApiClient.getMode() === 'MOCK';

    return {
      evaluatedAt: new Date().toISOString(),
      bottleneckCount: 1,
      networkVulnerabilityIndex: 28.4,
      nodes: [
        { id: 'NODE-T2-01', name: 'Gujarat Yarn Spinning Unit', tier: 'Tier-2 Supplier', location: 'Surat, Gujarat', status: 'HEALTHY', capacityUtilizationPercent: 78.0, holdingValueINR: 850000, throughputPerDay: 420, vulnerabilityScore: 18, x: 100, y: 120 },
        { id: 'NODE-T1-01', name: 'Apex Processing & Dyeing Mill', tier: 'Tier-1 Supplier', location: 'Tiruppur, TN', status: 'CONGESTED', capacityUtilizationPercent: 94.5, holdingValueINR: 1450000, throughputPerDay: 650, vulnerabilityScore: 64, x: 280, y: 120 },
        { id: 'NODE-MFG-01', name: 'Bengaluru Central Apparel Facility', tier: 'Manufacturing Plant', location: 'Peenya, Bengaluru', status: 'HEALTHY', capacityUtilizationPercent: 82.0, holdingValueINR: 3200000, throughputPerDay: 850, vulnerabilityScore: 24, x: 460, y: 120 },
        { id: 'NODE-DC-01', name: 'National Distribution Center (NDC)', tier: 'Central DC', location: 'Hosur Hub, TN', status: 'HEALTHY', capacityUtilizationPercent: 74.0, holdingValueINR: 2100000, throughputPerDay: 1200, vulnerabilityScore: 14, x: 640, y: 80 },
        { id: 'NODE-DC-02', name: 'North Fulfillment Hub', tier: 'Regional Hub', location: 'Gurugram, NCR', status: 'HEALTHY', capacityUtilizationPercent: 86.0, holdingValueINR: 1650000, throughputPerDay: 750, vulnerabilityScore: 32, x: 820, y: 80 },
        { id: 'NODE-RET-01', name: 'Omnichannel Retail & E-Com Nodes', tier: 'Customer Fulfillment', location: 'Pan-India Footprint', status: 'HEALTHY', capacityUtilizationPercent: 68.0, holdingValueINR: 950000, throughputPerDay: 1400, vulnerabilityScore: 10, x: 980, y: 120 },
      ],
      edges: [
        { id: 'EDGE-01', sourceNodeId: 'NODE-T2-01', targetNodeId: 'NODE-T1-01', flowVolumeUnitsPerMonth: 3200, leadTimeDays: 14, isBottleneck: false },
        { id: 'EDGE-02', sourceNodeId: 'NODE-T1-01', targetNodeId: 'NODE-MFG-01', flowVolumeUnitsPerMonth: 2800, leadTimeDays: 18, isBottleneck: true },
        { id: 'EDGE-03', sourceNodeId: 'NODE-MFG-01', targetNodeId: 'NODE-DC-01', flowVolumeUnitsPerMonth: 2400, leadTimeDays: 4, isBottleneck: false },
        { id: 'EDGE-04', sourceNodeId: 'NODE-DC-01', targetNodeId: 'NODE-DC-02', flowVolumeUnitsPerMonth: 1200, leadTimeDays: 3, isBottleneck: false },
        { id: 'EDGE-05', sourceNodeId: 'NODE-DC-01', targetNodeId: 'NODE-RET-01', flowVolumeUnitsPerMonth: 1200, leadTimeDays: 2, isBottleneck: false },
        { id: 'EDGE-06', sourceNodeId: 'NODE-DC-02', targetNodeId: 'NODE-RET-01', flowVolumeUnitsPerMonth: 900, leadTimeDays: 1, isBottleneck: false },
      ],
      bullwhipMetrics: [
        { tierName: 'Customer POS', tierOrder: 1, demandVariance: 14.2, orderVariance: 14.2, bullwhipRatio: 1.0, distortionRisk: 'STABLE' },
        { tierName: 'Regional Hub', tierOrder: 2, demandVariance: 14.2, orderVariance: 17.8, bullwhipRatio: 1.25, distortionRisk: 'STABLE' },
        { tierName: 'Central NDC', tierOrder: 3, demandVariance: 17.8, orderVariance: 24.6, bullwhipRatio: 1.38, distortionRisk: 'MODERATE' },
        { tierName: 'Manufacturing Plant', tierOrder: 4, demandVariance: 24.6, orderVariance: 39.4, bullwhipRatio: 1.60, distortionRisk: 'MODERATE' },
        { tierName: 'Tier-1 Supplier', tierOrder: 5, demandVariance: 39.4, orderVariance: 74.8, bullwhipRatio: 1.90, distortionRisk: 'SEVERE' },
      ],
      // STRICT MOCK GATE: Do not fake propagation in production
      simulatedPropagation: isMock ? {
        root_risk_entity: 'NODE-T1-01',
        total_downstream_entities_affected: 4,
        total_revenue_exposed_usd: 124500,
        propagation_path: [
          { hop: 1, entity_id: 'NODE-MFG-01', entity_name: 'Bengaluru Central Apparel Facility', entity_type: 'MANUFACTURING', financial_exposure_usd: 48000 },
          { hop: 2, entity_id: 'NODE-DC-01', entity_name: 'National Distribution Center (NDC)', entity_type: 'DISTRIBUTION', financial_exposure_usd: 35000 },
          { hop: 3, entity_id: 'NODE-DC-02', entity_name: 'North Fulfillment Hub', entity_type: 'REGIONAL_HUB', financial_exposure_usd: 21500 },
          { hop: 4, entity_id: 'NODE-RET-01', entity_name: 'Omnichannel Retail & E-Com Nodes', entity_type: 'FULFILLMENT', financial_exposure_usd: 20000 },
        ],
      } : undefined,
    };
  }
}
