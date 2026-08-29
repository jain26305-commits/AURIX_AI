import { ApiClient } from '@/services/api/apiClient';
import {
  DecisionSummaryDTO,
  UniversalDecisionCardDTO,
} from '@/types/decision.types';

export class DecisionService {
  public static async getSummary(periodKey: string = 'CURRENT'): Promise<DecisionSummaryDTO> {
    return ApiClient.get<DecisionSummaryDTO>(
      `/decisions/summary?period=${encodeURIComponent(periodKey)}`,
      () => ({
        tenantId: 'GLOBAL',
        periodKey: periodKey,
        totalDecisionsProposed: 12,
        pendingApprovalsCount: 4,
        executedDecisionsCount: 8,
        totalPipelineExpectedValueUsd: 148500.0,
        totalDownsideRiskMitigatedUsd: 62400.0,
        recommendationAcceptanceRatePct: 94.5,
        activeChampionModelsCount: 2,
        topDecisionDomain: 'PROCUREMENT_SUPPLIER',
        evaluatedAt: new Date().toISOString(),
      })
    );
  }

  public static async getCards(): Promise<UniversalDecisionCardDTO[]> {
    return ApiClient.get<UniversalDecisionCardDTO[]>('/decisions/cards', (): any[] => [
      {
        decisionId: 'DEC-001',
        tenantId: 'GLOBAL',
        decisionDomain: 'PROCUREMENT_SUPPLIER',
        decisionType: 'SUPPLIER_DISRUPTION_REMEDIATION',
        entityType: 'SUPPLIER',
        entityId: 'SUPP-01',
        title: 'Supplier Allocation Strategy: Apex Steel',
        whySummary: 'Primary supplier OTIF is 65.0% with 10 days port delay exposure.',
        recommendedAction: 'Split Order 60/40 with Backup Supplier',
        decisionState: 'PROPOSED',
        expectedValueUsd: 18400.0,
        downsideRiskUsd: 2000.0,
        confidenceScore: 0.94,
        financialImpactSummary: 'Generates net expected value of $18,400.00 against downside exposure of $2,000.00.',
        operationalImpactSummary: 'Preserves 98% commercial customer OTIF delivery commitment.',
        alternatives: [
          {
            candidateId: 'CND-01',
            actionCode: 'SPLIT_ORDER_ALLOCATION',
            actionName: 'Split Order 60/40 with Backup Supplier',
            description: 'Reallocate 40% volume to local secondary supplier.',
            benefitUsd: 20000.0,
            costUsd: 1600.0,
            riskPenaltyUsd: 2000.0,
            expectedValueUsd: 18400.0,
            utilityScore: 17080.0,
            isRecommended: true,
            constraintsSatisfied: { BUDGET_SATISFIED: true },
          },
        ],
        constraintsEvaluated: { BUDGET_COMPLIANCE: 'SATISFIED' },
        modelName: 'AURIX_SUPPLIER_ALLOC_V2',
        modelVersion: 'v2.0',
        approvalRequired: true,
        requiredApproverRole: 'PROCUREMENT_MANAGER',
        isReversible: true,
        createdAt: new Date().toISOString(),
      },
    ]);
  }
}
