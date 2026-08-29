'use client';

import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import {
  AtpInquiryResponse,
  FulfillmentReport,
  SalesChannel,
  SalesOrderStatus,
} from '@/types/fulfillment.types';
import { FulfillmentService } from '@/services/api/fulfillmentService';

export function useFulfillment() {
  const [statusFilter, setStatusFilter] =
    useState<SalesOrderStatus | 'ALL'>('ALL');

  const [channelFilter, setChannelFilter] =
    useState<SalesChannel | 'ALL'>('ALL');

  const [searchQuery, setSearchQuery] = useState<string>('');

  const [atpSkuId, setAtpSkuId] = useState<string>('SKU-004');
  const [atpUnits, setAtpUnits] = useState<number>(100);
  const [atpResult, setAtpResult] =
    useState<AtpInquiryResponse | null>(null);
  const [isCheckingAtp, setIsCheckingAtp] = useState<boolean>(false);

  const {
    data = null,
    isLoading,
    isFetching,
    refetch,
  } = useQuery<FulfillmentReport>({
    queryKey: ['fulfillment', 'report'],
    queryFn: FulfillmentService.fetchFulfillmentReport,
    staleTime: 60_000,
    refetchOnWindowFocus: false,
  });

  const handleCheckAtp = async () => {
    setIsCheckingAtp(true);

    try {
      const res = await FulfillmentService.checkAtp({
        skuId: atpSkuId,
        requestedUnits: atpUnits,
        targetDate: new Date().toISOString().split('T')[0],
      });

      setAtpResult(res);
    } catch (err) {
      console.error('[useFulfillment] ATP check failed:', err);
    } finally {
      setIsCheckingAtp(false);
    }
  };

  const filteredOrders = data
    ? data.orders.filter((ord) => {
        const matchesStatus =
          statusFilter === 'ALL' || ord.status === statusFilter;

        const matchesChannel =
          channelFilter === 'ALL' || ord.channel === channelFilter;

        const matchesSearch =
          searchQuery === '' ||
          ord.orderId.toLowerCase().includes(searchQuery.toLowerCase()) ||
          ord.customerName.toLowerCase().includes(searchQuery.toLowerCase()) ||
          ord.skuName.toLowerCase().includes(searchQuery.toLowerCase());

        return matchesStatus && matchesChannel && matchesSearch;
      })
    : [];

  return {
    data,
    loading: isLoading || isFetching,
    filteredOrders,
    statusFilter,
    setStatusFilter,
    channelFilter,
    setChannelFilter,
    searchQuery,
    setSearchQuery,
    atpSkuId,
    setAtpSkuId,
    atpUnits,
    setAtpUnits,
    atpResult,
    isCheckingAtp,
    handleCheckAtp,
    reload: async () => {
      await refetch();
    },
  };
}
