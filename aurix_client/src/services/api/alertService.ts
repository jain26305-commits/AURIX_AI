import { ApiClient } from '@/services/api/apiClient';
import { AlertFeedReport, AlertStatus } from '@/types/alert.types';
import { AlertAdapter } from '@/services/adapters/alertAdapter';

export class AlertService {
  public static async fetchAlertFeed(): Promise<AlertFeedReport> {
    return ApiClient.get<AlertFeedReport>(
      '/alerts/feed',
      () => AlertAdapter.generateSimulatedAlerts()
    );
  }

  public static async updateAlertStatus(alertId: string, status: AlertStatus): Promise<boolean> {
    return ApiClient.post<{ alertId: string; status: AlertStatus }, boolean>(
      `/alerts/${alertId}/status`,
      { alertId, status },
      () => true
    );
  }

  public static async escalateToCase(alertId: string): Promise<{ caseId: string }> {
    return ApiClient.post<{ alertId: string }, { caseId: string }>(
      `/alerts/${alertId}/escalate-case`,
      { alertId },
      () => ({ caseId: `CASE-2026-${Math.floor(1000 + Math.random() * 9000)}` })
    );
  }
}