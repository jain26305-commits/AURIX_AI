'use client';

import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import {
  InventoryAnalyticsReport,
  InventoryPolicyRecalculateResponse,
} from '@/types/inventory.types';
import { InventoryService } from '@/services/api/inventoryService';
import { useDebounce } from '@/hooks/useDebounce';

const INVENTORY_QUERY_KEY = ['inventory', 'analytics'] as const;

export function useInventoryOptimization() {
  const [selectedSkuId, setSelectedSkuId] = useState<string>('');
  const [simulatedServiceLevel, setSimulatedServiceLevel] =
    useState<number>(95);

  const inventoryQuery = useQuery<InventoryAnalyticsReport>({
    queryKey: INVENTORY_QUERY_KEY,
    queryFn: InventoryService.fetchInventoryAnalytics,
    staleTime: 60_000,
    refetchOnWindowFocus: false,
  });

  const data = inventoryQuery.data ?? null;

  const authoritativeSkuId =
    selectedSkuId ||
    data?.skuInventories?.[0]?.skuId ||
    '';

  const debouncedServiceLevel =
    useDebounce(simulatedServiceLevel, 300);

  const policyQuery = useQuery<InventoryPolicyRecalculateResponse>({
    queryKey: [
      'inventory',
      'policy-recalculation',
      authoritativeSkuId,
      debouncedServiceLevel,
    ],
    queryFn: () =>
      InventoryService.recalculatePolicy({
        skuId: authoritativeSkuId,
        serviceLevelTargetPercent: debouncedServiceLevel,
      }),
    enabled:
      Boolean(authoritativeSkuId) &&
      Boolean(data?.skuInventories?.length),
    staleTime: 0,
    refetchOnWindowFocus: false,
  });

  const activeSku =
    data?.skuInventories.find(
      (sku) => sku.skuId === authoritativeSkuId
    ) ??
    data?.skuInventories[0];

  const policyCalculation =
    policyQuery.data ?? null;

  return {
    data,
    loading:
      inventoryQuery.isLoading ||
      inventoryQuery.isFetching,
    isRecalculating:
      policyQuery.isLoading ||
      policyQuery.isFetching,
    selectedSkuId: authoritativeSkuId,
    setSelectedSkuId,
    activeSku,
    simulatedServiceLevel,
    setSimulatedServiceLevel,
    adjustedSafetyStock:
      policyCalculation?.computedSafetyStockUnits ??
      activeSku?.safetyStockUnits ??
      0,
    adjustedRop:
      policyCalculation?.computedReorderPointUnits ??
      activeSku?.reorderPointUnits ??
      0,
    policyCalculation,
    reload: async () => {
      await inventoryQuery.refetch();
    },
  };
}
