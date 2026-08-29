'use client';

import {
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query';
import { useState } from 'react';
import {
  AlertFeedReport,
  AlertSeverity,
  AlertStatus,
} from '@/types/alert.types';
import { AlertService } from '@/services/api/alertService';

const QUERY_KEY = ['alerts', 'feed'] as const;

export function useAlertsFeed() {
  const queryClient = useQueryClient();

  const [selectedSeverity, setSelectedSeverity] =
    useState<AlertSeverity | 'ALL'>('ALL');

  const [selectedStatus, setSelectedStatus] =
    useState<AlertStatus | 'ALL'>('ALL');

  const [searchQuery, setSearchQuery] = useState<string>('');

  const query = useQuery<AlertFeedReport>({
    queryKey: QUERY_KEY,
    queryFn: AlertService.fetchAlertFeed,
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });

  const acknowledgeMutation = useMutation({
    mutationFn: (alertId: string) =>
      AlertService.updateAlertStatus(alertId, 'ACKNOWLEDGED'),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: QUERY_KEY });
    },
  });

  const escalateMutation = useMutation({
    mutationFn: (alertId: string) =>
      AlertService.escalateToCase(alertId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: QUERY_KEY });
    },
  });

  const search = searchQuery.trim().toLowerCase();

  const filteredAlerts =
    query.data?.alerts.filter((alert) => {
      const matchesSeverity =
        selectedSeverity === 'ALL' ||
        alert.severity === selectedSeverity;

      const matchesStatus =
        selectedStatus === 'ALL' ||
        alert.status === selectedStatus;

      const matchesSearch =
        search === '' ||
        alert.title.toLowerCase().includes(search) ||
        alert.entityName.toLowerCase().includes(search) ||
        alert.entityId.toLowerCase().includes(search);

      return matchesSeverity && matchesStatus && matchesSearch;
    }) ?? [];

  return {
    data: query.data ?? null,
    loading: query.isLoading || query.isFetching,
    filteredAlerts,
    selectedSeverity,
    setSelectedSeverity,
    selectedStatus,
    setSelectedStatus,
    searchQuery,
    setSearchQuery,
    handleAcknowledge: acknowledgeMutation.mutateAsync,
    handleEscalate: escalateMutation.mutateAsync,
    reload: async () => {
      await query.refetch();
    },
  };
}
