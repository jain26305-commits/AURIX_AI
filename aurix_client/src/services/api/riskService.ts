import { ApiClient } from '@/services/api/apiClient';
import { RiskFindingDTO, RiskSummaryDTO } from '@/types/risk.types';

export class RiskService {
  public static async getSummary(periodKey: string = 'CURRENT'): Promise<RiskSummaryDTO> {
    return ApiClient.get<RiskSummaryDTO>(
      `/risk/summary?period=${encodeURIComponent(periodKey)}`,
      () => ({
        tenantId: 'GLOBAL',
        periodKey: periodKey,
        totalActiveRisksCount: 18,
        totalExposureUsd: 425000.0,
        totalExpectedLossUsd: 84200.0,
        criticalPrioritiesCount: 3,
        topRiskDomain: 'SUPPLIER',
        activeOpportunitiesCount: 5,
        totalOpportunityValueUsd: 128500.0,
        activeExternalSignalsCount: 2,
        overallRiskCoveragePct: 91.4,
        evaluatedAt: new Date().toISOString(),
      })
    );
  }

  public static async getPriorities(): Promise<RiskFindingDTO[]> {
    return ApiClient.get<RiskFindingDTO[]>('/risk/priorities', (): any[] => [
      {
        riskId: 'RSK-001',
        tenantId: 'GLOBAL',
        riskDomain: 'SUPPLIER',
        entityType: 'SUPPLIER',
        entityId: 'SUPP-01',
        title: 'Critical Port Disruption on Apex Steel',
        description: 'Port congestion at Singapore delays primary raw material shipment by 12 days.',
        probability: 0.85,
        impactAmountUsd: 150000.0,
        exposureAmountUsd: 127500.0,
        priorityScore: 14500.0,
        urgencyHours: 12.0,
        severity: 'CRITICAL',
        status: 'ACTIVE',
        firstDetected: new Date().toISOString(),
      },
    ]);
  }
}
