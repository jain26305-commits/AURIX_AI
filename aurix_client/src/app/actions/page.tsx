'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { ActionSummaryCards } from '@/components/features/actions/ActionSummaryCards';
import { ActionQueueTable } from '@/components/features/actions/ActionQueueTable';
import { PreflightCheckDrawer } from '@/components/features/actions/PreflightCheckDrawer';
import { ExecutionTokenModal } from '@/components/features/actions/ExecutionTokenModal';
import { useActionCenter } from '@/hooks/useActionCenter';
import { AurixButton } from '@/components/ui/AurixButton';
import { RotateCw, ArrowRight, Filter } from 'lucide-react';
import { ActionLifecycleState } from '@/types/action.types';
import { useWorkspaceHeader } from '@/context/WorkspaceHeaderContext';

export default function ActionsPage() {
  useWorkspaceHeader({ activeWorkspaceTitle: "Phase 14 Action Center" });
  const router = useRouter();
  const {
    data,
    loading,
    filteredActions,
    selectedState,
    setSelectedState,
    selectedActionForPreflight,
    setSelectedActionForPreflight,
    selectedActionForToken,
    setSelectedActionForToken,
    isProcessing,
    handleApprove,
    handleExecute,
    handleReject,
    reload,
  } = useActionCenter();

  if (loading || !data) {
    return (
      <>
        <div className="py-24 flex flex-col items-center justify-center text-center space-y-4 font-mono">
          <div className="w-8 h-8 rounded-full border-2 border-gold border-t-transparent animate-spin" />
          <p className="text-xs text-slate-400 tracking-widest uppercase">
            CONNECTING TO PHASE 14 ACTION EXECUTION GATEWAY...
          </p>
        </div>
      </>
    );
  }

  return (
    <>
      <div className="space-y-8 animate-pure-fade font-mono">
        {/* Header Block */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="px-2 py-0.5 rounded bg-gold/10 border border-gold/30 text-gold text-[10px] font-bold tracking-widest uppercase">
                AUTHORITATIVE EXECUTION GATEWAY
              </span>
              <span className="text-slate-500 text-xs">• PHASE 14 GOVERNANCE</span>
            </div>
            <h1 className="text-xl font-bold text-white tracking-wide">OPERATIONAL ACTION & DISPATCH CENTER</h1>
            <p className="text-xs text-slate-400 mt-0.5">
              Preflight clearance, cryptographic token signing, and authoritative ERP workflow dispatch.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <AurixButton variant="secondary" size="sm" onClick={reload}>
              <RotateCw className="w-3.5 h-3.5 mr-1.5" /> RE-SYNC
            </AurixButton>
            <AurixButton variant="gold" size="sm" onClick={() => router.push('/decisions/recommendations')}>
              <span>PREDICTIVE ADVISOR</span>
              <ArrowRight className="w-3.5 h-3.5 ml-1.5" />
            </AurixButton>
          </div>
        </div>

        {/* 1. Macro Summary Metric Cards */}
        <ActionSummaryCards summary={data.summary} />

        {/* 2. Lifecycle Filter Toolbar */}
        <div className="flex flex-wrap items-center justify-between gap-4 p-3 rounded-xl aurix-card-glass border border-white/[0.08] text-xs">
          <div className="flex items-center gap-2">
            <Filter className="w-3.5 h-3.5 text-gold" />
            <span className="text-slate-500 font-bold uppercase">LIFECYCLE STATE:</span>
            {(['ALL', 'AWAITING_APPROVAL', 'APPROVED', 'EXECUTED'] as const).map((st) => (
              <button
                key={st}
                onClick={() => setSelectedState(st as ActionLifecycleState | 'ALL')}
                className={`px-2.5 py-1 rounded-lg uppercase transition-colors cursor-pointer ${
                  selectedState === st ? 'bg-white/10 text-white font-bold' : 'text-slate-500 hover:text-slate-300'
                }`}
              >
                {st.replace('_', ' ')}
              </button>
            ))}
          </div>

          <div className="text-slate-400 text-[11px]">
            Showing <span className="text-white font-bold">{filteredActions.length}</span> Active Action Items
          </div>
        </div>

        {/* 3. Primary Action Execution Queue Table */}
        <ActionQueueTable
          actions={filteredActions}
          onOpenPreflight={(action) => setSelectedActionForPreflight(action)}
          onOpenToken={(action) => setSelectedActionForToken(action)}
          onExecute={handleExecute}
        />

        {/* 4. Preflight Check & Approval Drawer */}
        <PreflightCheckDrawer
          action={selectedActionForPreflight}
          isOpen={!!selectedActionForPreflight}
          onClose={() => setSelectedActionForPreflight(null)}
          onApprove={handleApprove}
          onReject={handleReject}
          isProcessing={isProcessing}
        />

        {/* 5. Cryptographic Execution Token Modal */}
        <ExecutionTokenModal
          token={selectedActionForToken?.executionToken}
          isOpen={!!selectedActionForToken}
          onClose={() => setSelectedActionForToken(null)}
        />
      </div>
    </>
  );
}