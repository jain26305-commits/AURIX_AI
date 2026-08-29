'use client';

import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import {
  AgentActivityReport,
  AgentTask,
} from '@/types/agent.types';
import { AgentService } from '@/services/api/agentService';

const QUERY_KEY = ['agents', 'activity'] as const;

export function useAgentActivity() {
  const [selectedTask, setSelectedTask] = useState<AgentTask | null>(null);

  const query = useQuery<AgentActivityReport>({
    queryKey: QUERY_KEY,
    queryFn: AgentService.fetchAgentActivity,
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });

  const effectiveSelectedTask =
    selectedTask ??
    query.data?.tasks?.[0] ??
    null;

  return {
    data: query.data ?? null,
    loading: query.isLoading || query.isFetching,
    selectedTask: effectiveSelectedTask,
    setSelectedTask,
    reload: async () => {
      await query.refetch();
    },
  };
}
