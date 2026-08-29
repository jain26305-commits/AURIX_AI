'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { ModelRegistryEntry } from '@/types/admin.types';
import { AdminService } from '@/services/api/adminService';

const QUERY_KEY = ['admin', 'models'] as const;

export function useAdminModels() {
  const queryClient = useQueryClient();
  const [retrainingId, setRetrainingId] = useState<string | null>(null);

  const query = useQuery<ModelRegistryEntry[]>({
    queryKey: QUERY_KEY,
    queryFn: AdminService.fetchModels,
    staleTime: 60_000,
    refetchOnWindowFocus: false,
  });

  const retrainMutation = useMutation({
    mutationFn: (modelId: string) =>
      AdminService.triggerModelRetraining(modelId),
    onMutate: (modelId) => {
      setRetrainingId(modelId);
    },
    onSettled: async () => {
      setRetrainingId(null);
      await queryClient.invalidateQueries({ queryKey: QUERY_KEY });
    },
  });

  return {
    models: query.data ?? [],
    loading: query.isLoading || query.isFetching,
    retrainingId,
    handleRetrain: retrainMutation.mutateAsync,
    reload: async () => {
      await query.refetch();
    },
  };
}
