'use client';

import { useQuery } from '@tanstack/react-query';
import { useMemo, useState } from 'react';
import {
  AdminUserRecord,
  SystemAuditLogEntry,
} from '@/types/admin.types';
import { AdminService } from '@/services/api/adminService';

const QUERY_KEY = ['admin', 'users'] as const;

interface AdminUsersData {
  users: AdminUserRecord[];
  auditLogs: SystemAuditLogEntry[];
}

export function useAdminUsers() {
  const [searchQuery, setSearchQuery] = useState<string>('');

  const query = useQuery<AdminUsersData>({
    queryKey: QUERY_KEY,
    queryFn: async () => {
      const [users, auditLogs] = await Promise.all([
        AdminService.fetchUsers(),
        AdminService.fetchAuditLogs(),
      ]);

      return { users, auditLogs };
    },
    staleTime: 60_000,
    refetchOnWindowFocus: false,
  });

  const auditLogs = query.data?.auditLogs ?? [];

  const filteredUsers = useMemo(() => {
    const users = query.data?.users ?? [];
    const search = searchQuery.trim().toLowerCase();

    if (!search) {
      return users;
    }

    return users.filter(
      (user) =>
        user.fullName.toLowerCase().includes(search) ||
        user.email.toLowerCase().includes(search) ||
        user.role.toLowerCase().includes(search)
    );
  }, [query.data?.users, searchQuery]);

  return {
    users: filteredUsers,
    auditLogs,
    loading: query.isLoading || query.isFetching,
    searchQuery,
    setSearchQuery,
    reload: async () => {
      await query.refetch();
    },
  };
}
