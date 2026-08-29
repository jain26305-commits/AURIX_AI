'use client';

import React, { useState } from 'react';
import { UserDirectoryTable } from '@/components/features/admin/UserDirectoryTable';
import { AuditLogTable } from '@/components/features/admin/AuditLogTable';
import { useAdminUsers } from '@/hooks/useAdminUsers';
import { AurixButton } from '@/components/ui/AurixButton';
import { RotateCw, Users, Search, History } from 'lucide-react';
import { useWorkspaceHeader } from '@/context/WorkspaceHeaderContext';

export default function UsersAdminPage() {
  useWorkspaceHeader({ activeWorkspaceTitle: "User & RBAC Administration" });
  const { users, auditLogs, loading, searchQuery, setSearchQuery, reload } = useAdminUsers();
  const [activeTab, setActiveTab] = useState<'USERS' | 'AUDIT_LOGS'>('USERS');

  if (loading) {
    return (
      <>
        <div className="py-24 flex flex-col items-center justify-center text-center space-y-4 font-mono">
          <div className="w-8 h-8 rounded-full border-2 border-gold border-t-transparent animate-spin" />
          <p className="text-xs text-slate-400 tracking-widest uppercase">LOADING RBAC USER DIRECTORY & AUDIT TRAIL...</p>
        </div>
      </>
    );
  }

  return (
    <>
      <div className="space-y-8 animate-pure-fade font-mono">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="px-2 py-0.5 rounded bg-gold/10 border border-gold/30 text-gold text-[10px] font-bold tracking-widest uppercase">
                SECURITY & GOVERNANCE
              </span>
              <span className="text-slate-500 text-xs">• POSTGRESQL RLS ENFORCED</span>
            </div>
            <h1 className="text-xl font-bold text-white tracking-wide">USER DIRECTORY, RBAC & AUDIT LOGS</h1>
            <p className="text-xs text-slate-400 mt-0.5">
              Manage enterprise user permissions, tenant memberships, and inspect the immutable security audit trail.
            </p>
          </div>

          <AurixButton variant="secondary" size="sm" onClick={reload}>
            <RotateCw className="w-3.5 h-3.5 mr-1.5" /> RE-SYNC
          </AurixButton>
        </div>

        {/* Sub-Domain Navigation Tabs */}
        <div className="flex items-center gap-2 p-1.5 bg-[#0C0E12] border border-white/[0.08] rounded-xl text-xs select-none">
          <button
            onClick={() => setActiveTab('USERS')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg font-bold transition-all cursor-pointer ${
              activeTab === 'USERS'
                ? 'bg-white/[0.08] text-white border border-white/20'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Users className={`w-3.5 h-3.5 ${activeTab === 'USERS' ? 'text-gold' : 'text-slate-500'}`} />
            <span>USER DIRECTORY ({users.length})</span>
          </button>

          <button
            onClick={() => setActiveTab('AUDIT_LOGS')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg font-bold transition-all cursor-pointer ${
              activeTab === 'AUDIT_LOGS'
                ? 'bg-white/[0.08] text-white border border-white/20'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <History className={`w-3.5 h-3.5 ${activeTab === 'AUDIT_LOGS' ? 'text-gold' : 'text-slate-500'}`} />
            <span>IMMUTABLE AUDIT LOG ({auditLogs.length})</span>
          </button>
        </div>

        {activeTab === 'USERS' && (
          <>
            <div className="relative w-full md:w-72">
              <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search user by name, email, role..."
                className="w-full bg-[#15171A] border border-white/10 rounded-lg pl-8 pr-3 py-1.5 text-white text-xs placeholder-slate-500 focus:outline-none focus:border-[#D4AF37]"
              />
            </div>
            <UserDirectoryTable users={users} />
          </>
        )}

        {activeTab === 'AUDIT_LOGS' && <AuditLogTable logs={auditLogs} />}
      </div>
    </>
  );
}