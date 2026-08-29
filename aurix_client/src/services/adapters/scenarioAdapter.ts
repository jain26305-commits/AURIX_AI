import { ScenarioSimulationSuite, ScenarioComparisonReport } from '@/types/scenario.types';
import { ApiClient } from '@/services/api/apiClient';

export class ScenarioAdapter {
  public static generateSimulatedSuite(): ScenarioSimulationSuite {
    return {
      suiteId: 'SUITE-DEFAULT',
      timestamp: new Date().toISOString(),
      baselineScenarioId: 'SCEN-BASELINE',
      baseScenario: {
        scenarioId: 'SCEN-BASELINE',
        name: 'Do-Nothing Production Control',
        description: 'Current operating trajectory with standard lead times and holding parameters.',
        outcomeDeltas: [],
        confidenceScorePct: 94,
        p50ValueUsd: 0,
        p90ValueUsd: 0,
      },
      simulatedBranches: [
        {
          scenarioId: 'SCEN-EXPEDITE',
          name: 'Air Freight PO Acceleration',
          description: 'Expedite Tier-1 replenishment via dedicated air corridors to protect fill rates.',
          outcomeDeltas: [
            {
              metric: 'Operating Margin',
              baselineValue: 120000,
              simulatedValue: 108000,
              deltaAbsolute: -12000,
              deltaPercent: -10,
              financialImpactUsd: -12000,
              unit: 'USD',
            },
            {
              metric: 'Service Level',
              baselineValue: 92,
              simulatedValue: 98.5,
              deltaAbsolute: 6.5,
              deltaPercent: 7.06,
              projectedServiceLevelPercent: 98.5,
              unit: '%',
            },
          ],
          confidenceScorePct: 91,
          p50ValueUsd: 34000,
          p90ValueUsd: 22000,
        },
      ],
      recommendedBranchId: 'SCEN-EXPEDITE',
    };
  }

  public static generateComparisonReport(): ScenarioComparisonReport | null {
    const isMock = ApiClient.getMode() === 'MOCK';
    if (!isMock) {
      return null;
    }

    return {
      tenant_id: ApiClient.getTenantId(),
      baseline_scenario_id: 'SCEN-BASELINE',
      recommended_scenario_id: 'SCEN-EXPEDITE',
      tradeoffs_explanation:
        'Scenario SCEN-EXPEDITE maximizes net Expected Value at $34,000.00 with mitigated revenue risk.',
      comparison_matrix: [
        {
          scenario_id: 'SCEN-BASELINE',
          is_baseline: true,
          revenue_usd: 500000,
          margin_usd: 120000,
          working_capital_usd: 150000,
          risk_exposure_usd: 45000,
          expected_value_usd: 0,
          confidence_score: 0.94,
        },
        {
          scenario_id: 'SCEN-EXPEDITE',
          is_baseline: false,
          revenue_usd: 540000,
          margin_usd: 108000,
          working_capital_usd: 135000,
          risk_exposure_usd: 12000,
          expected_value_usd: 34000,
          confidence_score: 0.91,
        },
        {
          scenario_id: 'SCEN-SPOT-BUY',
          is_baseline: false,
          revenue_usd: 520000,
          margin_usd: 96000,
          working_capital_usd: 160000,
          risk_exposure_usd: 18000,
          expected_value_usd: 14500,
          confidence_score: 0.84,
        },
      ],
    };
  }
}
