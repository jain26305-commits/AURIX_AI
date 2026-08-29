'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { AlertStatsBar } from '@/components/features/alerts/AlertStatsBar';
import { AlertFeedTable } from '@/components/features/alerts/AlertFeedTable';
import { useAlertsFeed } from '@/hooks/useAlertsFeed';
import { AurixButton } from '@/components/ui/AurixButton';
import { RotateCw, ArrowRight, Search, Filter } from 'lucide-react';
import { AlertSeverity } from '@/types/alert.types';
import { useWorkspaceHeader } from '@/context/WorkspaceHeaderContext';

export default function AlertsPage() {
  useWorkspaceHeader({ activeWorkspaceTitle: "Operational Alerts" });
  const router = useRouter();
  const {
    data,
    loading,
    filteredAlerts,
    selectedSeverity,
    setSelectedSeverity,
    searchQuery,
    setSearchQuery,
    handleAcknowledge,
    handleEscalate,
    reload,
  } = useAlertsFeed();

  if (loading || !data) {
    return (
      <>
        <div className="py-24 flex flex-col items-center justify-center text-center space-y-4 font-mono">
          <div className="w-8 h-8 rounded-full border-2 border-gold border-t-transparent animate-spin" />
          <p className="text-xs text-slate-400 tracking-widest uppercase">
            AUDITING CROSS-FUNCTIONAL OPERATIONAL ALERTS...
          </p>
        </div>
      </>
    );
  }

  return (
    <>
      <div className="space-y-8 animate-pure-fade">
        {/* Workspace Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-xl font-bold text-white tracking-wide">OPERATIONAL ALERTS & TRIAGE CENTER</h1>
            <p className="text-xs font-mono text-slate-400 mt-1">
              Deterministic threshold violations, lead-time variance alarms, and stockout breach signals.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <AurixButton variant="secondary" size="sm" onClick={reload}>
              <RotateCw className="w-3.5 h-3.5 mr-1.5" /> RE-AUDIT
            </AurixButton>
            <AurixButton variant="gold" size="sm" onClick={() => router.push('/risk-assurance/cases')}>
              <span>OPERATIONAL CASES</span>
              <ArrowRight className="w-3.5 h-3.5 ml-1.5" />
            </AurixButton>
          </div>
        </div>

        {/* 1. Macro Metric Summary Cards */}
        <AlertStatsBar summary={data.summary} />

        {/* 2. Filter & Search Controls */}
        <div className="flex flex-wrap items-center justify-between gap-4 p-3 rounded-xl aurix-card-glass border border-white/[0.08] text-xs font-mono">
          <div className="flex items-center gap-2">
            <Filter className="w-3.5 h-3.5 text-gold" />
            <span className="text-slate-500 font-bold uppercase">SEVERITY:</span>
            {(['ALL', 'CRITICAL', 'WARNING', 'INFO'] as const).map((sev) => (
              <button
                key={sev}
                onClick={() => setSelectedSeverity(sev as AlertSeverity | 'ALL')}
                className={`px-2.5 py-1 rounded-lg uppercase transition-colors cursor-pointer ${
                  selectedSeverity === sev ? 'bg-white/10 text-white font-bold' : 'text-slate-500 hover:text-slate-300'
                }`}
              >
                {sev}
              </button>
            ))}
          </div>

          <div className="flex items-center gap-2 w-full md:w-auto">
            <div className="relative flex-1 md:w-64">
              <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search alerts by SKU, lane, or rule..."
                className="w-full bg-[#15171A] border border-white/10 rounded-lg pl-8 pr-3 py-1.5 text-white placeholder-slate-500 focus:outline-none focus:border-[#D4AF37]"
              />
            </div>
          </div>
        </div>

        {/* 3. Primary Alerts Feed Table */}
        <AlertFeedTable
          alerts={filteredAlerts}
          onAcknowledge={handleAcknowledge}
          onEscalate={handleEscalate}
        />
      </div>
    </>
  );
}