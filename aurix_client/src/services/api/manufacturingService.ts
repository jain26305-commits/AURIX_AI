import { ApiClient } from '@/services/api/apiClient';
import { ManufacturingSummaryDTO } from '@/types/manufacturing.types';
import { ManufacturingAdapter } from '@/services/adapters/manufacturingAdapter';

export class ManufacturingService {
    public static async fetchManufacturingReport(): Promise<any> {
    return ApiClient.get<any>('/manufacturing/report', () =>
      ManufacturingAdapter.generateSimulatedManufacturing()
    );
  }

  public static async getSummary(periodKey: string = 'CURRENT'): Promise<ManufacturingSummaryDTO> {
    return ApiClient.get<ManufacturingSummaryDTO>(
      `/manufacturing/summary?period=${encodeURIComponent(periodKey)}`,
      () => ({
        tenantId: 'GLOBAL',
        periodKey: periodKey,
        totalWorkOrders: 42,
        activeWorkOrders: 18,
        plantCapacityUtilizationPct: 84.2,
        overallOeePct: 78.5,
        oeeStatus: 'AVAILABLE',
        firstPassYieldPct: 96.4,
        scrapRatePct: 2.1,
        totalDowntimeHours: 14.5,
        totalProductionRevenueAtRisk: 28500.0,
        bottleneckWorkCentersCount: 1,
        activeAnomaliesCount: 0,
        evaluatedAt: new Date().toISOString(),
      })
    );
  }
}
