'use client';

import { useQuery } from '@tanstack/react-query';
import {
  ProcessBottleneckDTO,
  ProcessSummaryDTO,
  ProcessVariantDTO,
} from '@/types/process.types';
import { ProcessService } from '@/services/api/processService';

interface ProcessIntelligenceQueryData {
  summary: ProcessSummaryDTO | null;
  bottlenecks: ProcessBottleneckDTO[];
  variants: ProcessVariantDTO[];
}

export function useProcessIntelligence() {
  const {
    data,
    isLoading,
    isFetching,
    refetch,
  } = useQuery<ProcessIntelligenceQueryData>({
    queryKey: ['process', 'intelligence'],
    queryFn: async () => {
      const [summary, bottlenecks, variants] = await Promise.all([
        ProcessService.getSummary(),
        ProcessService.getBottlenecks(),
        ProcessService.getVariants(),
      ]);

      return {
        summary,
        bottlenecks,
        variants,
      };
    },
    staleTime: 60_000,
    refetchOnWindowFocus: false,
  });

  return {
    summary: data?.summary ?? null,
    bottlenecks: data?.bottlenecks ?? [],
    variants: data?.variants ?? [],
    loading: isLoading || isFetching,
    reload: async () => {
      await refetch();
    },
  };
}
