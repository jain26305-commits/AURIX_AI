'use client';

import { useQuery } from '@tanstack/react-query';
import { ControlTowerReport } from '@/types/control-tower.types';
import { ControlTowerService } from '@/services/api/controlTowerService';

const QUERY_KEY = ['control-tower', 'snapshot'] as const;

export function useControlTower() {
  const query = useQuery<ControlTowerReport>({
    queryKey: QUERY_KEY,
    queryFn: ControlTowerService.fetchControlTowerSnapshot,
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });

  return {
    data: query.data ?? null,
    loading: query.isLoading || query.isFetching,
    reload: async () => {
      await query.refetch();
    },
  };
}
