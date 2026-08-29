'use client';

import { useQuery } from '@tanstack/react-query';
import { NetworkAnalyticsReport } from '@/types/network.types';
import { NetworkService } from '@/services/api/networkService';

export function useNetworkTopology() {
  const {
    data = null,
    isLoading,
    isFetching,
    refetch,
  } = useQuery<NetworkAnalyticsReport>({
    queryKey: ['network', 'topology'],
    queryFn: NetworkService.fetchNetworkTopology,
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
