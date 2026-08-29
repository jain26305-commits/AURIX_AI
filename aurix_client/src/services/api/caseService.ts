import { ApiClient } from '@/services/api/apiClient';
import { CaseManagementReport, CaseStage, OperationalCase } from '@/types/case.types';
import { CaseAdapter } from '@/services/adapters/caseAdapter';

export class CaseService {
  public static async fetchCaseReport(): Promise<CaseManagementReport> {
    return ApiClient.get<CaseManagementReport>(
      '/cases',
      () => CaseAdapter.generateSimulatedCases()
    );
  }

  public static async updateCaseStage(caseId: string, newStage: CaseStage): Promise<boolean> {
    return ApiClient.post<{ caseId: string; stage: CaseStage }, boolean>(
      `/cases/${caseId}/transition`,
      { caseId, stage: newStage },
      () => true
    );
  }

  public static async createCase(newCasePayload: Partial<OperationalCase>): Promise<OperationalCase> {
    return ApiClient.post<Partial<OperationalCase>, OperationalCase>(
      '/cases/create',
      newCasePayload,
      (body) => ({
        id: `CASE-2026-${Math.floor(1000 + Math.random() * 9000)}`,
        title: body.title || 'New Operational Case',
        domain: body.domain || 'Operational Risk',
        priority: body.priority || 'MEDIUM',
        stage: 'OPEN',
        owner: body.owner || 'Unassigned',
        targetEntityId: body.targetEntityId || 'SKU-001',
        targetEntityName: body.targetEntityName || 'Material Target',
        summary: body.summary || 'Operational deviation recorded.',
        rootCauseAttribution: body.rootCauseAttribution || 'Under analysis.',
        exposureINR: body.exposureINR || 0,
        serviceImpactPercent: body.serviceImpactPercent || 95.0,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        provenanceLineage: [
          {
            stepIndex: 1,
            stage: 'OPEN',
            title: 'Case Manually Provisioned',
            actorOrSystem: 'Operator Dispatch',
            timestamp: 'Just now',
            summary: 'Case initiated via AURIX Workspace.',
          },
        ],
      })
    );
  }
}