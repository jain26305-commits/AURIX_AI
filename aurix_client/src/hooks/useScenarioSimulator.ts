'use client';

import {
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query';
import { useState } from 'react';
import { ScenarioSimulationSuite } from '@/types/scenario.types';
import { ScenarioService } from '@/services/api/scenarioService';

const QUERY_KEY = ['scenarios', 'suite'] as const;

export function useScenarioSimulator() {
  const queryClient = useQueryClient();

  const [activeScenarioId, setActiveScenarioId] =
    useState<string | null>(null);

  const [leadTimeDelta, setLeadTimeDelta] =
    useState<number>(-7);

  const [serviceLevelTarget, setServiceLevelTarget] =
    useState<number>(98);

  const [demandSurge, setDemandSurge] =
    useState<number>(20);

  const suiteQuery = useQuery<ScenarioSimulationSuite>({
    queryKey: QUERY_KEY,
    queryFn: ScenarioService.fetchScenarioSuite,
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });

  const effectiveActiveScenarioId =
    activeScenarioId ??
    suiteQuery.data?.activeScenarioId ??
    suiteQuery.data?.baselineScenarioId ??
    'SCEN-EXPEDITE';

  const customSimulationMutation = useMutation({
    mutationFn: () =>
      ScenarioService.runCustomSimulation({
        scenarioId: 'SCEN-CUSTOM',
        name: 'Custom Parameter Simulation',
        branchType: 'CUSTOM_OVERRIDE',
        serviceLevelTargetPercent: serviceLevelTarget,
        leadTimeDaysDelta: leadTimeDelta,
        demandSurgeMultiplier: 1 + demandSurge / 100,
        unitCostAdjustmentPercent: 0,
        holdingRatePercent: 22,
        expediteActive: true,
      }),
    onSuccess: async (result) => {
      queryClient.setQueryData<ScenarioSimulationSuite>(
        QUERY_KEY,
        (previous) => {
          if (!previous) {
            return previous;
          }

          const branches =
            previous.simulatedBranches ?? [];

          const exists = branches.some(
            (branch) =>
              branch.scenarioId === 'SCEN-CUSTOM'
          );

          const simulatedBranches = exists
            ? branches.map((branch) =>
                branch.scenarioId === 'SCEN-CUSTOM'
                  ? result
                  : branch
              )
            : [...branches, result];

          return {
            ...previous,
            simulatedBranches,
          };
        }
      );

      setActiveScenarioId('SCEN-CUSTOM');
    },
  });

  const suite = suiteQuery.data ?? null;

  const activeScenario =
    suite?.simulatedBranches?.find(
      (branch) =>
        branch.scenarioId === effectiveActiveScenarioId
    ) ??
    suite?.baseScenario;

  return {
    suite,
    loading:
      suiteQuery.isLoading ||
      suiteQuery.isFetching,
    activeScenarioId: effectiveActiveScenarioId,
    setActiveScenarioId,
    activeScenario,
    leadTimeDelta,
    setLeadTimeDelta,
    serviceLevelTarget,
    setServiceLevelTarget,
    demandSurge,
    setDemandSurge,
    isSimulating:
      customSimulationMutation.isPending,
    runCustomWhatIf:
      customSimulationMutation.mutateAsync,
    reload: async () => {
      await suiteQuery.refetch();
    },
  };
}
