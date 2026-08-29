'use client';

import React from 'react';
import { CaseLifecycleBoard } from '@/components/features/cases/CaseLifecycleBoard';
import { CaseProvenanceTrace } from '@/components/features/cases/CaseProvenanceTrace';
import { CreateCaseModal } from '@/components/features/cases/CreateCaseModal';
import { useCaseManagement } from '@/hooks/useCaseManagement';
import { AurixButton } from '@/components/ui/AurixButton';
import { AurixCard } from '@/components/ui/AurixCard';
import { AurixBadge } from '@/components/ui/AurixBadge';
import { Plus, RotateCw } from 'lucide-react';
import { formatINR } from '@/lib/formatters';
import { useWorkspaceHeader } from '@/context/WorkspaceHeaderContext';

export default function CasesPage() {
  useWorkspaceHeader({ activeWorkspaceTitle: "Operational Cases" });
  const {
    data,
    loading,
    selectedCaseId,
    setSelectedCaseId,
    activeCase,
    isCreateModalOpen,
    setIsCreateModalOpen,
    handleTransitionStage,
    handleCreateCase,
    reload,
  } = useCaseManagement();

  if (loading || !data || !activeCase) {
    return (
      <>
        <div className="py-24 flex flex-col items-center justify-center text-center space-y-4 font-mono">
          <div className="w-8 h-8 rounded-full border-2 border-gold border-t-transparent animate-spin" />
          <p className="text-xs text-slate-400 tracking-widest uppercase">
            LOADING OPERATIONAL CASE LIFECYCLE REGISTRY...
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
            <h1 className="text-xl font-bold text-white tracking-wide">OPERATIONAL CASE MANAGEMENT (PHASE 16)</h1>
            <p className="text-xs font-mono text-slate-400 mt-1">
              End-to-end incident lifecycle governance from alert escalation to Phase 14 action execution.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <AurixButton variant="secondary" size="sm" onClick={reload}>
              <RotateCw className="w-3.5 h-3.5 mr-1.5" /> RE-SYNC
            </AurixButton>
            <AurixButton variant="gold" size="sm" onClick={() => setIsCreateModalOpen(true)}>
              <Plus className="w-3.5 h-3.5 mr-1.5" />
              <span>PROVISION CASE</span>
            </AurixButton>
          </div>
        </div>

        {/* Top Macro Summary Bar */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 select-none">
          <AurixCard title="ACTIVE CASES" badge={<AurixBadge variant="gold">INCIDENTS</AurixBadge>}>
            <div className="text-2xl font-bold font-mono text-white mt-2">0{data.summary.totalOpenCases}</div>
            <div className="text-[11px] font-mono text-slate-400 mt-1">Across Inventory & Logistics</div>
          </AurixCard>

          <AurixCard title="AWAITING APPROVAL" badge={<AurixBadge variant="warning">GOVERNANCE</AurixBadge>}>
            <div className="text-2xl font-bold font-mono text-[#F3B33D] mt-2">0{data.summary.awaitingApprovalCount}</div>
            <div className="text-[11px] font-mono text-slate-400 mt-1">Ready for executive signoff</div>
          </AurixCard>

          <AurixCard title="CRITICAL EXPOSURE" badge={<AurixBadge variant="danger" pulse>AT RISK</AurixBadge>}>
            <div className="text-2xl font-bold font-mono text-[#FF6B6B] mt-2">0{data.summary.criticalPriorityCount}</div>
            <div className="text-[11px] font-mono text-slate-400 mt-1">Critical priority incidents</div>
          </AurixCard>

          <AurixCard title="EXPOSURE AT STAKE" badge={<AurixBadge variant="info">FINANCIAL</AurixBadge>}>
            <div className="text-2xl font-bold font-mono text-[#D4AF37] mt-2">{formatINR(data.summary.aggregateExposureAtStakeINR)}</div>
            <div className="text-[11px] font-mono text-slate-400 mt-1">Total revenue under active case resolution</div>
          </AurixCard>
        </div>

        {/* 1. Kanban Lifecycle Board */}
        <CaseLifecycleBoard
          cases={data.cases}
          selectedCaseId={selectedCaseId}
          onSelectCase={setSelectedCaseId}
          onTransitionStage={handleTransitionStage}
        />

        {/* 2. Active Case Provenance & Root Cause Trace */}
        <CaseProvenanceTrace
          activeCase={activeCase}
          onTransitionStage={handleTransitionStage}
        />

        {/* 3. Create Case Modal */}
        <CreateCaseModal
          isOpen={isCreateModalOpen}
          onClose={() => setIsCreateModalOpen(false)}
          onSubmit={handleCreateCase}
        />
      </div>
    </>
  );
}