import { ApiClient } from '@/services/api/apiClient';
import { ExecutiveEightQuestionBriefDTO, ScenarioSummaryDTO } from '@/types/scenario.types';

export class ScenarioService {
    public static async fetchScenarioSuite(): Promise<any> {
    return ApiClient.get<any>('/scenarios/suite', () => ({
      suiteId: 'SUITE-DEFAULT',
      timestamp: new Date().toISOString(),
      baselineScenarioId: 'SCEN-DO-NOTHING',
      simulatedBranches: []
    }));
  }

  public static async runCustomSimulation(params: any): Promise<any> {
    return ApiClient.post<any, any>('/scenarios/simulate', params, () => ({
      scenarioId: 'SCEN-CUSTOM',
      name: 'Custom Simulated Branch',
      outcomeDeltas: []
    }));
  }

  public static async getSummary(periodKey: string = 'CURRENT'): Promise<ScenarioSummaryDTO> {
    return ApiClient.get<ScenarioSummaryDTO>(
      `/scenarios/summary?period=${encodeURIComponent(periodKey)}`,
      () => ({
        tenantId: 'GLOBAL',
        periodKey: periodKey,
        totalScenariosDefined: 6,
        activeSimulationsCount: 2,
        totalExpectedValuePipelineUsd: 168400.0,
        averagePredictionAccuracyPct: 91.5,
        activeCounterfactualTwinsCount: 3,
        overallSimulationReadinessPct: 95.0,
        evaluatedAt: new Date().toISOString(),
      })
    );
  }

  public static async getExecutiveBrief(): Promise<ExecutiveEightQuestionBriefDTO> {
    return ApiClient.get<ExecutiveEightQuestionBriefDTO>('/executive/brief', () => ({
      tenantId: 'GLOBAL',
      q1WhatHappened: 'Primary supplier Apex Steel experienced a 12-day maritime port delay.',
      q2WhyDidItHappen: 'Severe port congestion at Singapore (Congestion Index 85.0) stalled shipments.',
      q3WhatWillHappen: 'Production work order WO-100 will stall in 4 days, risking $75k customer revenue.',
      q4WhatCouldHappen: 'Worst-case tail risk (P90) could expand unfulfilled customer orders to $120k.',
      q5WhatShouldWeDo: 'Execute Decision DEC-001: Split order 60/40 with certified secondary vendor.',
      q6WhatIfWeDoNothing: 'Doing nothing results in $45k OTIF penalty and customer churn risk.',
      q7WhatIsTheExpectedValue: 'Generates net Expected Value of $18,400.00 (Confidence 94%).',
      q8DidTheActionWork: 'Action executed successfully, recovering $16,200.00 in realized business value.',
      generatedAt: new Date().toISOString(),
    }));
  }
}
