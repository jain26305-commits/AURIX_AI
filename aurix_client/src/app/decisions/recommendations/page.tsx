'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { RecommendationCard } from '@/components/features/recommendations/RecommendationCard';
import { ActionApprovalModal } from '@/components/features/recommendations/ActionApprovalModal';
import { ProvenanceTraceDrawer } from '@/components/features/recommendations/ProvenanceTraceDrawer';
import { useRecommendationPipeline } from '@/hooks/useRecommendationPipeline';
import { AurixCard } from '@/components/ui/AurixCard';
import { AurixBadge } from '@/components/ui/AurixBadge';
import { AurixButton } from '@/components/ui/AurixButton';
import { ArrowRight, RotateCw, Filter } from 'lucide-react';
import { useWorkspaceHeader } from '@/context/WorkspaceHeaderContext';

export default function RecommendationsPage() {
  useWorkspaceHeader({ activeWorkspaceTitle: "AI Decision Advisor" });
  const router = useRouter();
  const {
    data,
    loading,
    severityFilter,
    setSeverityFilter,
    filteredItems,
    activeItemForApproval,
    setActiveItemForApproval,
    activeItemForProvenance,
    setActiveItemForProvenance,
    isProcessingAction,
    executeStatusChange,
    reload,
  } = useRecommendationPipeline();

  if (loading || !data) {
    return (
      <>
        <div className="py-24 flex flex-col items-center justify-center text-center space-y-4">
          <div className="w-8 h-8 rounded-full border-2 border-gold border-t-transparent animate-spin" />
          <p className="text-xs font-mono text-slate-400 tracking-widest uppercase">
            SYNTHESIZING PRESCRIPTIVE AI RECOMMENDATIONS...
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
            <h1 className="text-xl font-bold text-white tracking-wide">AI RECOMMENDATION & DECISION CENTER</h1>
            <p className="text-xs font-mono text-slate-400 mt-1">
              Contextual prescriptive advisor with human-in-the-loop governance and explainability provenance.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <AurixButton variant="secondary" size="sm" onClick={reload}>
              <RotateCw className="w-3.5 h-3.5 mr-1.5" /> RE-EVALUATE
            </AurixButton>
            <AurixButton variant="gold" size="sm" onClick={() => router.push('/control-tower')}>
              <span>VIEW CONTROL TOWER</span>
              <ArrowRight className="w-3.5 h-3.5 ml-1.5" />
            </AurixButton>
          </div>
        </div>

        {/* Top Summary KPI Ribbon */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <AurixCard title="ACTIVE SIGNALS" badge={<AurixBadge variant="info">PIPELINE</AurixBadge>}>
            <div className="text-2xl font-bold font-mono text-white mt-2">
              0{data.summary.totalSignalsActive} Prescriptions
            </div>
            <div className="text-[11px] font-mono text-slate-400 mt-1">Across Inventory, Supply & Freight</div>
          </AurixCard>

          <AurixCard title="CRITICAL EXPOSURE" badge={<AurixBadge variant="danger" pulse>ACTION REQUIRED</AurixBadge>}>
            <div className="text-2xl font-bold font-mono text-[#FF6B6B] mt-2">
              0{data.summary.criticalActionCount} Critical
            </div>
            <div className="text-[11px] font-mono text-slate-400 mt-1">Projected breach in &lt; 7 days</div>
          </AurixCard>

          <AurixCard title="AVOIDABLE LOSS" badge={<AurixBadge variant="gold">ROI CONDUIT</AurixBadge>}>
            <div className="text-2xl font-bold font-mono text-gold mt-2">
              ₹{(data.summary.totalExposureAvoidableINR / 100000).toFixed(2)}L
            </div>
            <div className="text-[11px] font-mono text-slate-400 mt-1">Gross exposure averted</div>
          </AurixCard>

          <AurixCard title="PENDING APPROVALS" badge={<AurixBadge variant="warning">GOVERNANCE</AurixBadge>}>
            <div className="text-2xl font-bold font-mono text-[#F3B33D] mt-2">
              0{data.summary.pendingApprovalsCount} Awaiting
            </div>
            <div className="text-[11px] font-mono text-slate-400 mt-1">Human-in-the-loop signoff</div>
          </AurixCard>
        </div>

        {/* Filter Toolbar */}
        <div className="flex flex-wrap items-center justify-between gap-4 p-3 rounded-xl aurix-card-glass border border-white/[0.08] text-xs font-mono">
          <div className="flex items-center gap-2">
            <Filter className="w-3.5 h-3.5 text-gold" />
            <span className="text-slate-500 font-bold uppercase">FILTER SEVERITY:</span>
            {(['all', 'CRITICAL', 'HIGH', 'WATCH'] as const).map((sev) => (
              <button
                key={sev}
                onClick={() => setSeverityFilter(sev)}
                className={`px-2.5 py-1 rounded-lg uppercase transition-colors cursor-pointer ${
                  severityFilter === sev ? 'bg-white/10 text-white font-bold' : 'text-slate-500 hover:text-slate-300'
                }`}
              >
                {sev}
              </button>
            ))}
          </div>

          <div className="text-slate-400 text-[11px]">
            Showing <span className="text-white font-bold">{filteredItems.length}</span> of {data.recommendations.length} Active Prescriptions
          </div>
        </div>

        {/* Primary Recommendations Feed */}
        <div className="space-y-6">
          {filteredItems.map((item) => (
            <RecommendationCard
              key={item.id}
              item={item}
              onOpenApproval={() => setActiveItemForApproval(item)}
              onOpenProvenance={() => setActiveItemForProvenance(item)}
              onReject={() => executeStatusChange(item.id, 'REJECTED')}
              onSimulate={() => router.push('/decisions/scenarios')}
            />
          ))}
        </div>

        {/* Human-in-the-Loop Signoff Modal */}
        <ActionApprovalModal
          item={activeItemForApproval}
          isOpen={!!activeItemForApproval}
          onClose={() => setActiveItemForApproval(null)}
          onConfirmApprove={(id) => executeStatusChange(id, 'APPROVED')}
          isProcessing={isProcessingAction}
        />

        {/* Provenance Deep-Dive Drawer */}
        <ProvenanceTraceDrawer
          item={activeItemForProvenance}
          isOpen={!!activeItemForProvenance}
          onClose={() => setActiveItemForProvenance(null)}
        />
      </div>
    </>
  );
}