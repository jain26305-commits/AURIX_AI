import { ApiClient } from '@/services/api/apiClient';
import { LogisticsAnalyticsReport } from '@/types/logistics.types';
import { LogisticsAdapter } from '@/services/adapters/logisticsAdapter';

export class LogisticsService {
  public static async fetchLogisticsAnalytics(): Promise<LogisticsAnalyticsReport> {
    return ApiClient.get<LogisticsAnalyticsReport>(
      '/logistics/analytics',
      () => LogisticsAdapter.generateSimulatedLogistics()
    );
  }
}