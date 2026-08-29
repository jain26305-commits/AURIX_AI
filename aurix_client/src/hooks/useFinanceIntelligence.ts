'use client';

import { useQuery } from '@tanstack/react-query';
import { FinancialExposureReport } from '@/types/finance.types';
import { FinanceService } from '@/services/api/financeService';

const FINANCE_EXPOSURE_QUERY_KEY = ['finance', 'financial-exposure'] as const;

export function useFinanceIntelligence() {
  const {
    data = null,
    isLoading,
    isFetching,
    error,
    refetch,
  } = useQuery<FinancialExposureReport>({
    queryKey: FINANCE_EXPOSURE_QUERY_KEY,
    queryFn: FinanceService.fetchFinancialExposure,
    staleTime: 60_000,
    refetchOnWindowFocus: false,
  });

  const reload = async () => {
    await refetch();
  };

  return {
    data,
    loading: isLoading || isFetching,
    error,
    reload,
  };
}