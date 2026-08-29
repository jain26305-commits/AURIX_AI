import { SupplyAnalyticsReport } from '@/types/supply.types';
import { SupplyAdapter } from '@/services/adapters/supplyAdapter';

export class SupplyService {
  public static async fetchSupplyAnalytics(): Promise<SupplyAnalyticsReport> {
    await new Promise((resolve) => setTimeout(resolve, 500));
    return SupplyAdapter.generateSimulatedSupply();
  }
}