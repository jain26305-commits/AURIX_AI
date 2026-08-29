'use client';

import { useQuery } from '@tanstack/react-query';
import { LogisticsAnalyticsReport } from '@/types/logistics.types';
import { LogisticsService } from '@/services/api/logisticsService';

export function useLogisticsIntelligence() {
  const {
    data = null,
    isLoading,
    isFetching,
    refetch,
  } = useQuery<LogisticsAnalyticsReport>({
    queryKey: ['logistics', 'analytics'],
    queryFn: LogisticsService.fetchLogisticsAnalytics,
    staleTime: 60_000,
    refetchOnWindowFocus: false,
  });

  return {
    data,
    loading: isLoading || isFetching,
    reload: async () => {
      await refetch();
    },
  };
}
