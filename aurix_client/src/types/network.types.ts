export interface NetworkTopologyNode {
  id: string;
  name: string;
  tier: string;
  location: string;
  status: 'HEALTHY' | 'CONGESTED' | 'DISRUPTED';
  capacityUtilizationPercent: number;
  holdingValueINR: number;
  throughputPerDay: number;
  vulnerabilityScore: number;
  x: number;
  y: number;
}

export interface NetworkTopologyEdge {
  id: string;
  sourceNodeId: string;
  targetNodeId: string;
  flowVolumeUnitsPerMonth: number;
  leadTimeDays: number;
  isBottleneck: boolean;
}

export interface BullwhipTierMetric {
  tierName: string;
  tierOrder: number;
  demandVariance: number;
  orderVariance: number;
  bullwhipRatio: number;
  distortionRisk: 'STABLE' | 'MODERATE' | 'SEVERE';
}

export interface AffectedEntity {
  hop: number;
  entity_id: string;
  entity_name: string;
  entity_type: string;
  financial_exposure_usd: number;
}

export interface DisruptionPropagationPath {
  root_risk_entity: string;
  total_downstream_entities_affected: number;
  total_revenue_exposed_usd: number;
  propagation_path: AffectedEntity[];
}

export interface NetworkAnalyticsReport {
  evaluatedAt: string;
  nodes: NetworkTopologyNode[];
  edges: NetworkTopologyEdge[];
  bullwhipMetrics: BullwhipTierMetric[];
  bottleneckCount: number;
  networkVulnerabilityIndex: number;
  simulatedPropagation?: DisruptionPropagationPath;
}
