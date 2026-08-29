import { ApiClient } from '@/services/api/apiClient';
import {
  AdminUserRecord,
  EnterpriseConnector,
  ModelRegistryEntry,
  SystemAuditLogEntry,
  SystemHealthReport,
} from '@/types/admin.types';
import { AdminAdapter } from '@/services/adapters/adminAdapter';

export class AdminService {
  public static async fetchConnectors(): Promise<EnterpriseConnector[]> {
    return ApiClient.get<EnterpriseConnector[]>(
      '/admin/integrations',
      () => AdminAdapter.generateSimulatedConnectors()
    );
  }

  public static async triggerConnectorSync(connectorId: string): Promise<boolean> {
    const res = await ApiClient.post<{ connectorId: string }, { status: string }>(
      `/admin/integrations/${connectorId}/sync`,
      { connectorId },
      () => ({ status: 'COMPLETED' })
    );
    return res.status === 'COMPLETED';
  }

  public static async fetchModels(): Promise<ModelRegistryEntry[]> {
    return ApiClient.get<ModelRegistryEntry[]>(
      '/admin/models',
      () => AdminAdapter.generateSimulatedModels()
    );
  }

  public static async triggerModelRetraining(modelId: string): Promise<boolean> {
    const res = await ApiClient.post<{ modelId: string }, { success: boolean }>(
      `/admin/models/${modelId}/retrain`,
      { modelId },
      () => ({ success: true })
    );
    return res.success;
  }

  public static async fetchSystemHealth(): Promise<SystemHealthReport> {
    return ApiClient.get<SystemHealthReport>(
      '/admin/system-health',
      () => AdminAdapter.generateSimulatedSystemHealth()
    );
  }

  public static async fetchUsers(): Promise<AdminUserRecord[]> {
    return ApiClient.get<AdminUserRecord[]>(
      '/admin/users',
      () => AdminAdapter.generateSimulatedUsers()
    );
  }

  public static async fetchAuditLogs(): Promise<SystemAuditLogEntry[]> {
    return ApiClient.get<SystemAuditLogEntry[]>(
      '/admin/audit-logs',
      () => AdminAdapter.generateSimulatedAuditLogs()
    );
  }
}