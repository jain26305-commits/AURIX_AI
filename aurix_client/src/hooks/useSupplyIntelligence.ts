'use client';

import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import { SupplyAnalyticsReport } from '@/types/supply.types';
import { SupplyService } from '@/services/api/supplyService';

export function useSupplyIntelligence() {
  const [selectedVendorId, setSelectedVendorId] =
    useState<string>('VEND-001');

  const {
    data = null,
    isLoading,
    isFetching,
    refetch,
  } = useQuery<SupplyAnalyticsReport>({
    queryKey: ['supply', 'analytics'],
    queryFn: SupplyService.fetchSupplyAnalytics,
    staleTime: 60_000,
    refetchOnWindowFocus: false,
  });

  const activeVendor =
    data?.suppliers.find((supplier) => supplier.supplierId === selectedVendorId) ||
    data?.suppliers[0];

  return {
    data,
    loading: isLoading || isFetching,
    selectedVendorId,
    setSelectedVendorId,
    activeVendor,
    reload: async () => {
      await refetch();
    },
  };
}
