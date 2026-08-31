'use client';

import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import {
  ForecastAnalyticsPayload,
  ForecastHorizon,
} from '@/types/forecast.types';
import { ForecastService } from '@/services/api/forecastService';
import {
  useSkuWorkspaceContext,
} from '@/context/SkuWorkspaceContext';

export function useForecastEngine() {
  const {
    selectedSkuId,
    setSelectedSkuId,
  } = useSkuWorkspaceContext();

  const [horizon, setHorizon] =
    useState<ForecastHorizon>('3M');

  const [isDrawerOpen, setIsDrawerOpen] =
    useState<boolean>(false);

  const {
    data = null,
    isLoading,
    isFetching,
    refetch,
  } = useQuery<ForecastAnalyticsPayload>({
    queryKey: [
      'forecast',
      'analytics',
      selectedSkuId,
      horizon,
    ],
    queryFn: () =>
      ForecastService.fetchForecastForSku(
        selectedSkuId,
        horizon
      ),
    enabled: Boolean(selectedSkuId),
    staleTime: 60_000,
    refetchOnWindowFocus: false,
  });

  return {
    data,
    loading:
      isLoading ||
      isFetching,
    skuId: selectedSkuId,
    setSkuId: setSelectedSkuId,
    horizon,
    setHorizon,
    isDrawerOpen,
    setIsDrawerOpen,
    reload: async () => {
      await refetch();
    },
  };
}
