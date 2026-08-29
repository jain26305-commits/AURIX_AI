'use client';

import { useQuery } from '@tanstack/react-query';
import { RiskFindingDTO, RiskSummaryDTO } from '@/types/risk.types';
import { AssuranceFindingDTO } from '@/types/assurance.types';
import { RiskService } from '@/services/api/riskService';
import { AssuranceService } from '@/services/api/assuranceService';

interface RiskAssuranceQueryData {
  riskSummary: RiskSummaryDTO | null;
  priorities: RiskFindingDTO[];
  findings: AssuranceFindingDTO[];
}

export function useRiskAssurance() {
  const {
    data,
    isLoading,
    isFetching,
    refetch,
  } = useQuery<RiskAssuranceQueryData>({
    queryKey: ['risk-assurance', 'overview'],
    queryFn: async () => {
      const [riskSummary, priorities, findings] = await Promise.all([
        RiskService.getSummary(),
        RiskService.getPriorities(),
        AssuranceService.getFindings(),
      ]);

      return {
        riskSummary,
        priorities,
        findings,
      };
    },
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });

  return {
    riskSummary: data?.riskSummary ?? null,
    priorities: data?.priorities ?? [],
    findings: data?.findings ?? [],
    loading: isLoading || isFetching,
    reload: async () => {
      await refetch();
    },
  };
}
