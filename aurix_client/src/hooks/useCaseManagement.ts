'use client';

import {
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query';
import { useState } from 'react';
import {
  CaseManagementReport,
  CaseStage,
  OperationalCase,
} from '@/types/case.types';
import { CaseService } from '@/services/api/caseService';

const QUERY_KEY = ['cases', 'management'] as const;

export function useCaseManagement() {
  const queryClient = useQueryClient();

  const [selectedCaseId, setSelectedCaseId] =
    useState<string | null>(null);

  const [isCreateModalOpen, setIsCreateModalOpen] =
    useState<boolean>(false);

  const query = useQuery<CaseManagementReport>({
    queryKey: QUERY_KEY,
    queryFn: CaseService.fetchCaseReport,
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });

  const transitionMutation = useMutation({
    mutationFn: ({
      caseId,
      newStage,
    }: {
      caseId: string;
      newStage: CaseStage;
    }) => CaseService.updateCaseStage(caseId, newStage),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: QUERY_KEY });
    },
  });

  const createMutation = useMutation({
    mutationFn: (payload: Partial<OperationalCase>) =>
      CaseService.createCase(payload),
    onSuccess: async (created) => {
      setSelectedCaseId(created.id);
      setIsCreateModalOpen(false);
      await queryClient.invalidateQueries({ queryKey: QUERY_KEY });
    },
  });

  const effectiveSelectedCaseId =
    selectedCaseId ??
    query.data?.cases?.[0]?.id ??
    null;

  const activeCase =
    query.data?.cases.find(
      (caseItem) => caseItem.id === effectiveSelectedCaseId
    ) ??
    query.data?.cases?.[0] ??
    null;

  return {
    data: query.data ?? null,
    loading: query.isLoading || query.isFetching,
    selectedCaseId: effectiveSelectedCaseId,
    setSelectedCaseId,
    activeCase,
    isCreateModalOpen,
    setIsCreateModalOpen,
    handleTransitionStage: async (
      caseId: string,
      newStage: CaseStage
    ) => {
      await transitionMutation.mutateAsync({ caseId, newStage });
    },
    handleCreateCase: async (
      newCasePayload: Partial<OperationalCase>
    ) => {
      await createMutation.mutateAsync(newCasePayload);
    },
    reload: async () => {
      await query.refetch();
    },
  };
}
