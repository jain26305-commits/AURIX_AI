export type PillarStatus = 'OPTIMAL' | 'WATCH' | 'CRITICAL';

export interface PillarHealthItem {
  key: string;
  title: string;
  status: PillarStatus;
  primaryMetric: string;
  metricLabel: string;
  subText: string;
  routeHref: string;
}

export interface UrgentSignalItem {
  id: string;
  title: string;
  targetEntity: string;
  category: string;
  severity: 'CRITICAL' | 'HIGH' | 'WATCH';
  exposureINR: number;
  breachWindow: string;
  prescriptiveSummary: string;
  recommendationRoute: string;
}

export interface ExecutiveFinancialSnapshot {
  grossInventoryValuationINR: number;
  unlockedCapitalOpportunityINR: number;
  stockoutRevenueAtRiskINR: number;
  portfolioServiceLevelPercent: number;
  serviceLevelTargetPercent: number;
  activeBreachesCount: number;
}

export interface ControlTowerReport {
  evaluatedAt: string;
  engineSyncStatus: 'SYNCHRONIZED' | 'PROCESSING' | 'OFFLINE';
  tenantId: string;
  financials: ExecutiveFinancialSnapshot;
  pillars: PillarHealthItem[];
  urgentSignals: UrgentSignalItem[];
}