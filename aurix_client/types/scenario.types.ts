export interface ScenarioOutcomeDelta {
  scenarioId?: string;
  name?: string;
  branchType?: string;
  metric?: string;
  baselineValue?: number;
  simulatedValue?: number;
  deltaAbsolute?: number;
  deltaPercent?: number;
  financialImpactUsd?: number;
  projectedServiceLevelPercent?: number;
  serviceLevelDeltaPercent?: number;
  totalWorkingCapitalINR?: number;
  workingCapitalDeltaINR?: number;
  strategicRationale?: string;
  unit?: string;
  [key: string]: any;
}

export interface ScenarioBranchDTO {
  scenarioId?: string;
  name?: string;
  description?: string;
  outcomeDeltas?: ScenarioOutcomeDelta[];
  confidenceScorePct?: number;
  p50ValueUsd?: number;
  p90ValueUsd?: number;
  [key: string]: any;
}

export interface ScenarioSimulationSuite {
  suiteId?: string;
  timestamp?: string;
  baselineScenarioId?: string;
  simulatedBranches?: any[];
  baseScenario?: any;
  recommendedBranchId?: string;
  [key: string]: any;
}

export interface CounterfactualRecordDTO {
  decisionId?: string;
  scenarioId?: string;
  historicalDelta?: number;
  [key: string]: any;
}

export interface ExecutiveEightQuestionBriefDTO {
  briefId?: string;
  summaryText?: string;
  [key: string]: any;
}

export interface ScenarioResultDTO {
  resultId?: string;
  confidenceScore?: number;
  [key: string]: any;
}

export interface ScenarioSummaryDTO {
  totalSimulations?: number;
  activeBranchesCount?: number;
  [key: string]: any;
}
