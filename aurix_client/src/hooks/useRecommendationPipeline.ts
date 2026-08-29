'use client';

import {
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query';
import { useState } from 'react';
import {
  RecommendationFeedReport,
  RecommendationItem,
  SignalSeverity,
  WorkflowStatus,
  ActionCategory,
} from '@/types/recommendation.types';
import { RecommendationService } from '@/services/api/recommendationService';

const QUERY_KEY = ['recommendations', 'feed'] as const;

export function useRecommendationPipeline() {
  const queryClient = useQueryClient();

  const [severityFilter, setSeverityFilter] =
    useState<SignalSeverity | 'all'>('all');

  const [categoryFilter, setCategoryFilter] =
    useState<ActionCategory | 'all'>('all');

  const [activeItemForApproval, setActiveItemForApproval] =
    useState<RecommendationItem | null>(null);

  const [activeItemForProvenance, setActiveItemForProvenance] =
    useState<RecommendationItem | null>(null);

  const feedQuery = useQuery<RecommendationFeedReport>({
    queryKey: QUERY_KEY,
    queryFn: RecommendationService.fetchRecommendationFeed,
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });

  const statusMutation = useMutation({
    mutationFn: ({
      itemId,
      newStatus,
    }: {
      itemId: string;
      newStatus: WorkflowStatus;
    }) =>
      RecommendationService.updateActionStatus(
        itemId,
        newStatus
      ),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: QUERY_KEY,
      });

      setActiveItemForApproval(null);
    },
  });

  const data = feedQuery.data;

  const filteredItems =
    data?.recommendations.filter((item) => {
      const matchesSeverity =
        severityFilter === 'all' ||
        item.severity === severityFilter;

      const matchesCategory =
        categoryFilter === 'all' ||
        item.category === categoryFilter;

      return matchesSeverity && matchesCategory;
    }) ?? [];

  return {
    data: data ?? null,
    loading:
      feedQuery.isLoading ||
      feedQuery.isFetching,
    severityFilter,
    setSeverityFilter,
    categoryFilter,
    setCategoryFilter,
    filteredItems,
    activeItemForApproval,
    setActiveItemForApproval,
    activeItemForProvenance,
    setActiveItemForProvenance,
    isProcessingAction: statusMutation.isPending,
    executeStatusChange: async (
      itemId: string,
      newStatus: WorkflowStatus
    ) => {
      await statusMutation.mutateAsync({
        itemId,
        newStatus,
      });
    },
    reload: async () => {
      await feedQuery.refetch();
    },
  };
}
