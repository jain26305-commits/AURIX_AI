import { ApiClient } from '@/services/api/apiClient';
import { SalesAnalyticsReport } from '@/types/sales.types';
import { SalesAdapter } from '@/services/adapters/salesAdapter';

export class SalesService {
  public static async fetchSalesAnalytics(): Promise<SalesAnalyticsReport> {
    return ApiClient.get<SalesAnalyticsReport>(
      '/sales/analytics',
      () => SalesAdapter.generateSimulatedSales()
    );
  }
}
