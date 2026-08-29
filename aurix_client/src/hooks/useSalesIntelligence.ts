'use client';

import { useQuery } from '@tanstack/react-query';
import { SalesAnalyticsReport } from '@/types/sales.types';
import { SalesService } from '@/services/api/salesService';

export function useSalesIntelligence() {
  const {
    data = null,
    isLoading,
    isFetching,
    refetch,
  } = useQuery<SalesAnalyticsReport>({
    queryKey: ['sales', 'analytics'],
    queryFn: SalesService.fetchSalesAnalytics,
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
