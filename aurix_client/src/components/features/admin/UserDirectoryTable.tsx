'use client';

import React from 'react';
import { AdminUserRecord } from '@/types/admin.types';
import { AurixBadge } from '@/components/ui/AurixBadge';
import { ShieldCheck, User } from 'lucide-react';

export const UserDirectoryTable: React.FC<{ users: AdminUserRecord[] }> = ({ users }) => {
  return (
    <div className="w-full aurix-card-glass rounded-xl p-6 border border-white/[0.08] select-none font-mono">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="border-b border-white/[0.08] text-slate-500 text-[10px] uppercase tracking-wider">
              <th className="pb-3 pl-2">User Profile</th>
              <th className="pb-3">Assigned Role</th>
              <th className="pb-3">Tenant Scope</th>
              <th className="pb-3">Last Session</th>
              <th className="pb-3">MFA Status</th>
              <th className="pb-3 text-right pr-2">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/[0.04]">
            {users.map((u) => (
              <tr key={u.userId} className="hover:bg-white/[0.02] transition-colors">
                <td className="py-3.5 pl-2">
                  <div className="flex items-center gap-2.5">
                    <div className="p-1.5 rounded-full bg-white/[0.05] border border-white/10 text-gold">
                      <User className="w-3.5 h-3.5" />
                    </div>
                    <div>
                      <span className="text-white font-bold text-xs block">{u.fullName}</span>
                      <span className="text-slate-500 text-[10px]">{u.email}</span>
                    </div>
                  </div>
                </td>

                <td className="py-3.5">
                  <AurixBadge variant={u.role === 'SUPER_ADMIN' ? 'gold' : u.role === 'EXECUTIVE' ? 'info' : 'neutral'}>
                    {u.role}
                  </AurixBadge>
                </td>

                <td className="py-3.5 text-slate-300">{u.tenantId}</td>

                <td className="py-3.5 text-slate-400">{u.lastLoginAt}</td>

                <td className="py-3.5">
                  <span className="text-[#3DDB91] text-[10px] font-bold flex items-center gap-1">
                    <ShieldCheck className="w-3 h-3" /> ENFORCED
                  </span>
                </td>

                <td className="py-3.5 text-right pr-2">
                  <AurixBadge variant={u.status === 'ACTIVE' ? 'success' : 'warning'}>
                    {u.status}
                  </AurixBadge>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};