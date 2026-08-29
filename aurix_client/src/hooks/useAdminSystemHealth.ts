'use client';

import { useQuery } from '@tanstack/react-query';
import { SystemHealthReport } from '@/types/admin.types';
import { AdminService } from '@/services/api/adminService';

const QUERY_KEY = ['admin', 'system-health'] as const;

export function useAdminSystemHealth() {
  const query = useQuery<SystemHealthReport>({
    queryKey: QUERY_KEY,
    queryFn: AdminService.fetchSystemHealth,
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });

  return {
    report: query.data ?? null,
    loading: query.isLoading || query.isFetching,
    reload: async () => {
      await query.refetch();
    },
  };
}
