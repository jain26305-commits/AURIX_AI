'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { EnterpriseConnector } from '@/types/admin.types';
import { AdminService } from '@/services/api/adminService';

const QUERY_KEY = ['admin', 'connectors'] as const;

export function useAdminIntegrations() {
  const queryClient = useQueryClient();
  const [syncingId, setSyncingId] = useState<string | null>(null);

  const query = useQuery<EnterpriseConnector[]>({
    queryKey: QUERY_KEY,
    queryFn: AdminService.fetchConnectors,
    staleTime: 60_000,
    refetchOnWindowFocus: false,
  });

  const syncMutation = useMutation({
    mutationFn: (connectorId: string) =>
      AdminService.triggerConnectorSync(connectorId),
    onMutate: (connectorId) => {
      setSyncingId(connectorId);
    },
    onSettled: async () => {
      setSyncingId(null);
      await queryClient.invalidateQueries({ queryKey: QUERY_KEY });
    },
  });

  return {
    connectors: query.data ?? [],
    loading: query.isLoading || query.isFetching,
    syncingId,
    handleSync: syncMutation.mutateAsync,
    reload: async () => {
      await query.refetch();
    },
  };
}
