'use client';

import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import { ForecastAnalyticsPayload, ForecastHorizon } from '@/types/forecast.types';
import { ForecastService } from '@/services/api/forecastService';

export function useForecastEngine(initialSku: string = 'SKU-001') {
  const [skuId, setSkuId] = useState<string>(initialSku);
  const [horizon, setHorizon] = useState<ForecastHorizon>('3M');
  const [isDrawerOpen, setIsDrawerOpen] = useState<boolean>(false);

  const {
    data = null,
    isLoading,
    isFetching,
    refetch,
  } = useQuery<ForecastAnalyticsPayload>({
    queryKey: ['forecast', 'analytics', skuId, horizon],
    queryFn: () => ForecastService.fetchForecastForSku(skuId, horizon),
    enabled: Boolean(skuId),
    staleTime: 60_000,
    refetchOnWindowFocus: false,
  });

  return {
    data,
    loading: isLoading || isFetching,
    skuId,
    setSkuId,
    horizon,
    setHorizon,
    isDrawerOpen,
    setIsDrawerOpen,
    reload: async () => {
      await refetch();
    },
  };
}
