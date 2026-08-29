'use client';

import { useQuery } from '@tanstack/react-query';
import {
  ProcurementReport,
  PoLifecycleStatus,
  ThreeWayMatchStatus,
} from '@/types/procurement.types';
import { ProcurementService } from '@/services/api/procurementService';
import { useState } from 'react';

export function useProcurement() {
  const [activeTab, setActiveTab] = useState<
    'ORDERS' | 'THREE_WAY_MATCH' | 'ASN_TRACKING'
  >('ORDERS');

  const [poStatusFilter, setPoStatusFilter] =
    useState<PoLifecycleStatus | 'ALL'>('ALL');

  const [matchStatusFilter, setMatchStatusFilter] =
    useState<ThreeWayMatchStatus | 'ALL'>('ALL');

  const [searchQuery, setSearchQuery] = useState<string>('');

  const {
    data = null,
    isLoading,
    isFetching,
    refetch,
  } = useQuery<ProcurementReport>({
    queryKey: ['procurement', 'report'],
    queryFn: ProcurementService.fetchProcurementReport,
    staleTime: 60_000,
    refetchOnWindowFocus: false,
  });

  const filteredOrders = data
    ? data.purchaseOrders.filter((po) => {
        const matchesStatus =
          poStatusFilter === 'ALL' || po.status === poStatusFilter;

        const matchesSearch =
          searchQuery === '' ||
          po.poNumber.toLowerCase().includes(searchQuery.toLowerCase()) ||
          po.vendorName.toLowerCase().includes(searchQuery.toLowerCase());

        return matchesStatus && matchesSearch;
      })
    : [];

  const filteredMatches = data
    ? data.matches.filter((m) => {
        const matchesStatus =
          matchStatusFilter === 'ALL' || m.status === matchStatusFilter;

        const matchesSearch =
          searchQuery === '' ||
          m.poNumber.toLowerCase().includes(searchQuery.toLowerCase()) ||
          m.invoiceNumber.toLowerCase().includes(searchQuery.toLowerCase()) ||
          m.vendorName.toLowerCase().includes(searchQuery.toLowerCase());

        return matchesStatus && matchesSearch;
      })
    : [];

  return {
    data,
    loading: isLoading || isFetching,
    activeTab,
    setActiveTab,
    poStatusFilter,
    setPoStatusFilter,
    matchStatusFilter,
    setMatchStatusFilter,
    searchQuery,
    setSearchQuery,
    filteredOrders,
    filteredMatches,
    reload: async () => {
      await refetch();
    },
  };
}
