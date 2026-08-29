export type TransportMode = 'Road Freight' | 'Air Cargo' | 'Ocean Express' | 'Rail Transport';
export type ShipmentStatus = 'IN_TRANSIT' | 'CUSTOMS_HOLD' | 'OUT_FOR_DELIVERY' | 'DELIVERED' | 'DELAYED';
export type LaneRiskLevel = 'LOW' | 'MODERATE' | 'CRITICAL';

export interface ActiveShipment {
  trackingId: string;
  poNumber: string;
  originHub: string;
  destinationHub: string;
  transportMode: TransportMode;
  carrierName: string;
  skuCount: number;
  totalUnits: number;
  shipmentValueINR: number;
  status: ShipmentStatus;
  dispatchedDate: string;
  estimatedArrival: string;
  delayVarianceDays: number;
  delayProbabilityPercent: number;
}

export interface TransitLaneMetrics {
  laneId: string;
  origin: string;
  destination: string;
  mode: TransportMode;
  avgTransitDays: number;
  p90TransitDays: number;
  onTimeReliabilityPercent: number;
  riskLevel: LaneRiskLevel;
  activeShipmentsCount: number;
  totalUnitsInTransit: number;
  totalCapitalInTransitINR: number;
}

export interface LogisticsSummaryMetrics {
  totalActiveShipments: number;
  totalInTransitUnits: number;
  totalInTransitValuationINR: number;
  shipmentsAtDelayRiskCount: number;
  portfolioOnTimeTransitPercent: number;
}

export interface LogisticsAnalyticsReport {
  evaluatedAt: string;
  summary: LogisticsSummaryMetrics;
  lanes: TransitLaneMetrics[];
  shipments: ActiveShipment[];
}