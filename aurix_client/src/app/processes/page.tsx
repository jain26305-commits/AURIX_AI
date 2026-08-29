'use client';

import React from 'react';
import { DomainWorkspaceOrchestrator } from '@/components/domain/DomainWorkspaceOrchestrator';
import { useProcessIntelligence } from '@/hooks/useProcessIntelligence';
import { ProcessGraphView } from '@/components/visualizations/ProcessGraphView';
import { AurixCard } from '@/components/ui/AurixCard';
import { AurixBadge } from '@/components/ui/AurixBadge';
import { GitFork, Clock, AlertTriangle } from 'lucide-react';

function ProcessesWorkspace({ subdomainId }: { subdomainId: string }) {
  const { summary, bottlenecks, variants, loading } = useProcessIntelligence();

  if (loading || !summary) {
    return (
      <div className="py-24 flex flex-col items-center justify-center text-center space-y-4 font-mono">
        <div className="w-8 h-8 rounded-full border-2 border-gold border-t-transparent animate-spin" />
        <p className="text-xs text-slate-400 tracking-widest uppercase">MINING EVENT LOGS FOR PROCESS VARIANTS...</p>
      </div>
    );
  }

  if (subdomainId === 'mining') {
    return <ProcessGraphView />;
  }

  if (subdomainId === 'variants') {
    return (
      <AurixCard
        title="DEVIANT PATHWAY & VARIANT DISCOVERY"
        badge={<AurixBadge variant="gold">{summary.discoveredVariantsCount} VARIANTS</AurixBadge>}
      >
        <div className="space-y-3 pt-2 font-mono text-xs">
          {variants.map((v) => (
            <div
              key={v.variantId}
              className={`p-4 rounded-xl border ${
                v.isStandardPath ? 'bg-white/[0.02] border-white/[0.06]' : 'bg-[#F3B33D]/5 border-[#F3B33D]/25'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-white font-bold">{v.processType.replace(/_/g, ' ')}</span>
                <div className="flex items-center gap-2">
                  {!v.isStandardPath && <AurixBadge variant="warning" size="sm">DEVIANT PATH</AurixBadge>}
                  <span className="text-slate-400">{v.frequencyPct}% · {v.caseCount} cases</span>
                </div>
              </div>
              <div className="flex items-center flex-wrap gap-1.5 text-[10px] text-slate-400">
                {v.stepSequence.map((step, i) => (
                  <React.Fragment key={i}>
                    <span className={`px-2 py-1 rounded ${v.isStandardPath ? 'bg-white/5' : 'bg-[#F3B33D]/10 text-[#F3B33D]'}`}>{step}</span>
                    {i < v.stepSequence.length - 1 && <span className="text-slate-600">→</span>}
                  </React.Fragment>
                ))}
              </div>
              <div className="mt-2 text-[10px] text-slate-500">AVG DURATION: {v.averageDurationHours.toFixed(1)}h</div>
            </div>
          ))}
        </div>
      </AurixCard>
    );
  }

  if (subdomainId === 'bottlenecks') {
    return (
      <AurixCard title="SLA BOTTLENECK INSPECTION" badge={<AurixBadge variant="danger">{summary.topBottleneckStep}</AurixBadge>}>
        <div className="space-y-3 pt-2 font-mono text-xs">
          {bottlenecks.map((b) => (
            <div key={b.bottleneckId} className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.06]">
              <div className="flex items-center justify-between mb-2">
                <span className="text-white font-bold flex items-center gap-1.5">
                  <AlertTriangle className={`w-3.5 h-3.5 ${b.severity === 'HIGH' ? 'text-[#FF6B6B]' : b.severity === 'MEDIUM' ? 'text-[#F3B33D]' : 'text-slate-500'}`} />
                  {b.stepName}
                </span>
                <AurixBadge variant={b.severity === 'HIGH' ? 'danger' : b.severity === 'MEDIUM' ? 'warning' : 'success'} size="sm">
                  {b.severity}
                </AurixBadge>
              </div>
              <div className="grid grid-cols-3 gap-3 text-[10px] mb-2">
                <div><span className="text-slate-500 block">QUEUE DEPTH</span><span className="text-white font-bold">{b.queueDepthCases} cases</span></div>
                <div><span className="text-slate-500 block">AVG WAIT</span><span className="text-white font-bold">{b.averageWaitingHours}h</span></div>
                <div><span className="text-slate-500 block">SLA BREACH</span><span className="text-[#F3B33D] font-bold">{b.slaBreachRatePct}%</span></div>
              </div>
              <p className="text-slate-400 font-sans leading-relaxed">{b.primaryFrictionCause}</p>
              <div className="mt-2 text-[10px] text-gold">ANNUALIZED DRAG: ${b.annualizedFinancialDrag.toLocaleString()}</div>
            </div>
          ))}
        </div>
      </AurixCard>
    );
  }

  if (subdomainId === 'cycle-time') {
    return (
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <AurixCard title="ORDER-TO-CASH CYCLE TIME" badge={<AurixBadge variant="success">{summary.averageO2cCycleDays}d MEDIAN</AurixBadge>}>
          <div className="flex items-center justify-center py-6">
            <Clock className="w-10 h-10 text-gold" />
          </div>
          <p className="text-slate-400 font-sans text-xs leading-relaxed text-center">
            Average order-to-cash cycle across {summary.activeCasesCount} active cases, from order placement
            through payment reconciliation.
          </p>
        </AurixCard>
        <AurixCard title="PROCURE-TO-PAY CYCLE TIME" badge={<AurixBadge variant="gold">{summary.averageP2pCycleDays}d MEDIAN</AurixBadge>}>
          <div className="flex items-center justify-center py-6">
            <GitFork className="w-10 h-10 text-gold" />
          </div>
          <p className="text-slate-400 font-sans text-xs leading-relaxed text-center">
            Average procure-to-pay cycle from PO creation through settlement, including approval routing
            and 3-way match reconciliation delays.
          </p>
        </AurixCard>
      </div>
    );
  }

  return null;
}

export default function ProcessesPage() {
  return (
    <DomainWorkspaceOrchestrator
      domainKey="processes"
      renderWorkspace={(subdomainId) => <ProcessesWorkspace subdomainId={subdomainId} />}
    />
  );
}
