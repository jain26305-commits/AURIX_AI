'use client';

import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import {
  Account360DTO,
  CommercialOTIFDTO,
  CommercialSummaryDTO,
  PVMDecompositionDTO,
} from '@/types/commercial.types';
import { CommercialService } from '@/services/api/commercialService';

interface CommercialIntelligenceData {
  summary: CommercialSummaryDTO;
  accounts: Account360DTO[];
  otif: CommercialOTIFDTO;
  pvm: PVMDecompositionDTO;
}

const QUERY_KEY = ['commercial', 'intelligence'] as const;

export function useCommercialIntelligence() {
  const [selectedAccountId, setSelectedAccountId] =
    useState<string | null>(null);

  const query = useQuery<CommercialIntelligenceData>({
    queryKey: QUERY_KEY,
    queryFn: async () => {
      const [summary, accounts, otif, pvm] = await Promise.all([
        CommercialService.getSummary(),
        CommercialService.getAccounts(),
        CommercialService.getOtif(),
        CommercialService.getPvm(),
      ]);

      return {
        summary,
        accounts,
        otif,
        pvm,
      };
    },
    staleTime: 60_000,
    refetchOnWindowFocus: false,
  });

  const accounts = query.data?.accounts ?? [];

  const effectiveSelectedAccountId =
    selectedAccountId ?? accounts[0]?.customerId ?? null;

  const selectedAccount =
    accounts.find(
      (account) =>
        account.customerId === effectiveSelectedAccountId
    ) ??
    accounts[0] ??
    null;

  return {
    summary: query.data?.summary ?? null,
    accounts,
    otif: query.data?.otif ?? null,
    pvm: query.data?.pvm ?? null,
    loading: query.isLoading || query.isFetching,
    selectedAccountId: effectiveSelectedAccountId,
    setSelectedAccountId,
    selectedAccount,
    reload: async () => {
      await query.refetch();
    },
  };
}
