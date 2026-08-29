'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import {
  ActionCenterFeedReport,
  ActionLifecycleState,
  Phase14ActionItem,
} from '@/types/action.types';
import { ActionService } from '@/services/api/actionService';

const QUERY_KEY = ['actions', 'feed'] as const;

export function useActionCenter() {
  const queryClient = useQueryClient();

  const [selectedState, setSelectedState] =
    useState<ActionLifecycleState | 'ALL'>('ALL');

  const [selectedActionForPreflight, setSelectedActionForPreflight] =
    useState<Phase14ActionItem | null>(null);

  const [selectedActionForToken, setSelectedActionForToken] =
    useState<Phase14ActionItem | null>(null);

  const query = useQuery<ActionCenterFeedReport>({
    queryKey: QUERY_KEY,
    queryFn: ActionService.fetchActionFeed,
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });

  const approveMutation = useMutation({
    mutationFn: (actionId: string) =>
      ActionService.approveAction(actionId),
    onSuccess: async () => {
      setSelectedActionForPreflight(null);
      await queryClient.invalidateQueries({ queryKey: QUERY_KEY });
    },
  });

  const executeMutation = useMutation({
    mutationFn: (actionId: string) =>
      ActionService.executeAction(actionId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: QUERY_KEY });
    },
  });

  const rejectMutation = useMutation({
    mutationFn: ({
      actionId,
      reason,
    }: {
      actionId: string;
      reason: string;
    }) => ActionService.rejectAction(actionId, reason),
    onSuccess: async () => {
      setSelectedActionForPreflight(null);
      await queryClient.invalidateQueries({ queryKey: QUERY_KEY });
    },
  });

  const filteredActions =
    query.data?.actions.filter((action) =>
      selectedState === 'ALL'
        ? true
        : action.state === selectedState
    ) ?? [];

  return {
    data: query.data ?? null,
    loading: query.isLoading || query.isFetching,
    filteredActions,
    selectedState,
    setSelectedState,
    selectedActionForPreflight,
    setSelectedActionForPreflight,
    selectedActionForToken,
    setSelectedActionForToken,
    isProcessing:
      approveMutation.isPending ||
      executeMutation.isPending ||
      rejectMutation.isPending,
    handleApprove: approveMutation.mutateAsync,
    handleExecute: executeMutation.mutateAsync,
    handleReject: async (actionId: string, reason: string) =>
      rejectMutation.mutateAsync({ actionId, reason }),
    reload: async () => {
      await query.refetch();
    },
  };
}
