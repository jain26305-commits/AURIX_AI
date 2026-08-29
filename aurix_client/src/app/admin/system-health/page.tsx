'use client';

import React from 'react';
import { HealthRadarCards } from '@/components/features/admin/HealthRadarCards';
import { useAdminSystemHealth } from '@/hooks/useAdminSystemHealth';
import { AurixButton } from '@/components/ui/AurixButton';
import { RotateCw } from 'lucide-react';
import { useWorkspaceHeader } from '@/context/WorkspaceHeaderContext';

export default function SystemHealthPage() {
  useWorkspaceHeader({ activeWorkspaceTitle: "System Health" });
  const { report, loading, reload } = useAdminSystemHealth();

  if (loading || !report) {
    return (
      <>
        <div className="py-24 flex flex-col items-center justify-center text-center space-y-4 font-mono">
          <div className="w-8 h-8 rounded-full border-2 border-gold border-t-transparent animate-spin" />
          <p className="text-xs text-slate-400 tracking-widest uppercase">POLLING INFRASTRUCTURE TELEMETRY...</p>
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
                OBSERVABILITY & RUNTIME
              </span>
              <span className="text-slate-500 text-xs">• MICROSERVICE TELEMETRY</span>
            </div>
            <h1 className="text-xl font-bold text-white tracking-wide">SYSTEM HEALTH & INFRASTRUCTURE MONITOR</h1>
            <p className="text-xs text-slate-400 mt-0.5">
              Live API latencies, PostgreSQL RLS connection pools, Redis queue depths, and worker node health.
            </p>
          </div>

          <AurixButton variant="secondary" size="sm" onClick={reload}>
            <RotateCw className="w-3.5 h-3.5 mr-1.5" /> RE-POLL
          </AurixButton>
        </div>

        <HealthRadarCards report={report} />
      </div>
    </>
  );
}