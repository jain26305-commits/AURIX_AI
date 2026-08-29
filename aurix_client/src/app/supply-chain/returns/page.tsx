'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { ReturnsStatsBar } from '@/components/features/returns/ReturnsStatsBar';
import { ReturnsTable } from '@/components/features/returns/ReturnsTable';
import { DispositionSummaryCard } from '@/components/features/returns/DispositionSummaryCard';
import { useReturns } from '@/hooks/useReturns';
import { AurixButton } from '@/components/ui/AurixButton';
import { RotateCw, ArrowRight, Filter, Search } from 'lucide-react';
import { ReturnDisposition } from '@/types/returns.types';
import { useWorkspaceHeader } from '@/context/WorkspaceHeaderContext';

export default function ReturnsPage() {
  useWorkspaceHeader({ activeWorkspaceTitle: "Reverse Logistics" });
  const router = useRouter();
  const {
    data,
    loading,
    filteredReturns,
    dispositionFilter,
    setDispositionFilter,
    searchQuery,
    setSearchQuery,
    reload,
  } = useReturns();

  if (loading || !data) {
    return (
      <>
        <div className="py-24 flex flex-col items-center justify-center text-center space-y-4 font-mono">
          <div className="w-8 h-8 rounded-full border-2 border-gold border-t-transparent animate-spin" />
          <p className="text-xs text-slate-400 tracking-widest uppercase">
            AUDITING REVERSE LOGISTICS & DISPOSITION RECOVERY...
          </p>
        </div>
      </>
    );
  }

  return (
    <>
      <div className="space-y-8 animate-pure-fade font-mono">
        {/* Workspace Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="px-2 py-0.5 rounded bg-gold/10 border border-gold/30 text-gold text-[10px] font-bold tracking-widest uppercase">
                REVERSE SUPPLY CHAIN
              </span>
              <span className="text-slate-500 text-xs">• RMA & DISPOSITION</span>
            </div>
            <h1 className="text-xl font-bold text-white tracking-wide">REVERSE LOGISTICS & RETURNS MANAGEMENT</h1>
            <p className="text-xs text-slate-400 mt-0.5">
              RMA intake records, root-cause defect categorization, and physical disposition recovery tracking.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <AurixButton variant="secondary" size="sm" onClick={reload}>
              <RotateCw className="w-3.5 h-3.5 mr-1.5" /> RE-AUDIT
            </AurixButton>
            <AurixButton variant="gold" size="sm" onClick={() => router.push('/supply-chain/fulfillment')}>
              <span>OUTBOUND FULFILLMENT</span>
              <ArrowRight className="w-3.5 h-3.5 ml-1.5" />
            </AurixButton>
          </div>
        </div>

        {/* 1. Macro Summary Cards */}
        <ReturnsStatsBar summary={data.summary} />

        {/* 2. Disposition & Salvage Recovery Summary */}
        <DispositionSummaryCard metrics={data.summary.dispositionMetrics} />

        {/* 3. Filter Toolbar */}
        <div className="flex flex-wrap items-center justify-between gap-4 p-3 rounded-xl aurix-card-glass border border-white/[0.08] text-xs">
          <div className="flex items-center gap-2">
            <Filter className="w-3.5 h-3.5 text-gold" />
            <span className="text-slate-500 font-bold uppercase">DISPOSITION:</span>
            {(['ALL', 'RESTOCK', 'REWORK', 'SCRAP'] as const).map((disp) => (
              <button
                key={disp}
                onClick={() => setDispositionFilter(disp as ReturnDisposition | 'ALL')}
                className={`px-2.5 py-1 rounded-lg uppercase transition-colors cursor-pointer ${
                  dispositionFilter === disp ? 'bg-white/10 text-white font-bold' : 'text-slate-500 hover:text-slate-300'
                }`}
              >
                {disp}
              </button>
            ))}
          </div>

          <div className="relative w-full md:w-64">
            <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search RMA or customer..."
              className="w-full bg-[#15171A] border border-white/10 rounded-lg pl-8 pr-3 py-1.5 text-white placeholder-slate-500 focus:outline-none focus:border-[#D4AF37]"
            />
          </div>
        </div>

        {/* 4. Returns Log Table */}
        <ReturnsTable returns={filteredReturns} />
      </div>
    </>
  );
}