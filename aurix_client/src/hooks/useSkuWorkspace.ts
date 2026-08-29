'use client';

import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import { SkuUnifiedStory } from '@/types/sku-workspace.types';
import { SkuWorkspaceService } from '@/services/api/skuWorkspaceService';

export function useSkuWorkspace(initialSkuId: string) {
  const [activeTab, setActiveTab] = useState<
    'FORECAST' | 'INVENTORY' | 'SUPPLY' | 'RECOMMENDATIONS'
  >('FORECAST');

  const {
    data: story = null,
    isLoading,
    isFetching,
    refetch,
  } = useQuery<SkuUnifiedStory>({
    queryKey: ['sku-workspace', initialSkuId],
    queryFn: () => SkuWorkspaceService.fetchSkuStory(initialSkuId),
    enabled: Boolean(initialSkuId),
    staleTime: 60_000,
    refetchOnWindowFocus: false,
  });

  return {
    story,
    loading: isLoading || isFetching,
    activeTab,
    setActiveTab,
    reload: async () => {
      await refetch();
    },
  };
}
