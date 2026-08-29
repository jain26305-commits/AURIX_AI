import { ApiClient } from '@/services/api/apiClient';
import {
  BusinessMemoryRecordDTO,
  ContextSummaryDTO,
} from '@/types/context.types';

export class ContextService {
  public static async getSummary(periodKey: string = 'CURRENT'): Promise<ContextSummaryDTO> {
    return ApiClient.get<ContextSummaryDTO>(
      `/context/summary?period=${encodeURIComponent(periodKey)}`,
      () => ({
        tenantId: 'GLOBAL',
        periodKey: periodKey,
        totalNodesCount: 248,
        totalEdgesCount: 512,
        activeMemoriesCount: 14,
        activeContractsCount: 2,
        overallReadinessPct: 92.5,
        businessDnaModel: 'CAPITAL_INTENSIVE_MANUFACTURING',
        evaluatedAt: new Date().toISOString(),
      })
    );
  }

  public static async getMemories(entityId?: string): Promise<BusinessMemoryRecordDTO[]> {
    const url = entityId ? `/context/memory?entity_id=${encodeURIComponent(entityId)}` : '/context/memory';
    return ApiClient.get<BusinessMemoryRecordDTO[]>(url, () => [
      {
        id: 'MEM-001',
        category: 'MANAGER_OVERRIDE',
        title: 'Expedited Supplier Freight Override',
        description: 'Manager approved 15% freight premium to bypass port congestion for customer Acme Corp.',
        contextEntityId: entityId || 'CUST-001',
        outcomeStatus: 'SUCCESSFUL',
        lessonsLearned: 'Saved $45k critical revenue penalty at cost of $1.5k expedited premium.',
        recordedBy: 'SYSTEM_GOVERNANCE',
        recordedAt: new Date().toISOString(),
      },
    ]);
  }
}
