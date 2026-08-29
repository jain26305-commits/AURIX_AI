'use client';

import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import {
  ReturnDisposition,
  ReturnReason,
  ReturnsReport,
} from '@/types/returns.types';
import { ReturnsService } from '@/services/api/returnsService';

export function useReturns() {
  const [dispositionFilter, setDispositionFilter] =
    useState<ReturnDisposition | 'ALL'>('ALL');

  const [reasonFilter, setReasonFilter] =
    useState<ReturnReason | 'ALL'>('ALL');

  const [searchQuery, setSearchQuery] = useState<string>('');

  const {
    data = null,
    isLoading,
    isFetching,
    refetch,
  } = useQuery<ReturnsReport>({
    queryKey: ['returns', 'report'],
    queryFn: ReturnsService.fetchReturnsReport,
    staleTime: 60_000,
    refetchOnWindowFocus: false,
  });

  const filteredReturns = data
    ? data.returns.filter((ret) => {
        const matchesDisposition =
          dispositionFilter === 'ALL' ||
          ret.disposition === dispositionFilter;

        const matchesReason =
          reasonFilter === 'ALL' ||
          ret.returnReason === reasonFilter;

        const matchesSearch =
          searchQuery === '' ||
          ret.rmaNumber.toLowerCase().includes(searchQuery.toLowerCase()) ||
          ret.orderId.toLowerCase().includes(searchQuery.toLowerCase()) ||
          ret.customerName.toLowerCase().includes(searchQuery.toLowerCase()) ||
          ret.skuName.toLowerCase().includes(searchQuery.toLowerCase());

        return matchesDisposition && matchesReason && matchesSearch;
      })
    : [];

  return {
    data,
    loading: isLoading || isFetching,
    filteredReturns,
    dispositionFilter,
    setDispositionFilter,
    reasonFilter,
    setReasonFilter,
    searchQuery,
    setSearchQuery,
    reload: async () => {
      await refetch();
    },
  };
}
