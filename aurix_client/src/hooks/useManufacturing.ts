'use client';

import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import { ManufacturingReport } from '@/types/manufacturing.types';
import { ManufacturingService } from '@/services/api/manufacturingService';
import {
  useSkuWorkspaceContext,
} from '@/context/SkuWorkspaceContext';

export function useManufacturing() {
  const [activeTab, setActiveTab] =
    useState<
      'BOM_EXPLORER' |
      'MRP_SCHEDULE' |
      'WORK_CENTERS' |
      'EXCEPTIONS'
    >('BOM_EXPLORER');

  const {
    selectedSkuId,
    setSelectedSkuId,
  } = useSkuWorkspaceContext();

  const {
    data = null,
    isLoading,
    isFetching,
    refetch,
  } = useQuery<ManufacturingReport>({
    queryKey: [
      'manufacturing',
      'report',
    ],
    queryFn:
      ManufacturingService.fetchManufacturingReport,
    staleTime: 60_000,
    refetchOnWindowFocus: false,
  });

  const effectiveSkuId =
    selectedSkuId ||
    data?.boms?.[0]?.parentSkuId ||
    '';

  const activeBom =
    (data?.boms || []).find(
      (b: any) =>
        b.parentSkuId ===
        effectiveSkuId
    ) ||
    (data?.boms || [])[0] ||
    null;

  const activeMrpPlan =
    (data?.mrpPlans || []).find(
      (m: any) =>
        m.skuId ===
        effectiveSkuId
    ) ||
    (data?.mrpPlans || [])[0] ||
    null;

  return {
    data,
    loading:
      isLoading ||
      isFetching,
    activeTab,
    setActiveTab,
    selectedSkuId:
      effectiveSkuId,
    setSelectedSkuId,
    activeBom,
    activeMrpPlan,
    reload: async () => {
      await refetch();
    },
  };
}
