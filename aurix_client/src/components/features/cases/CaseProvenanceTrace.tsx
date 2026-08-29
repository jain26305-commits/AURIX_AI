'use client';

import React from 'react';
import { OperationalCase, CaseStage } from '@/types/case.types';
import { AurixCard } from '@/components/ui/AurixCard';
import { AurixBadge } from '@/components/ui/AurixBadge';
import { AurixButton } from '@/components/ui/AurixButton';
import { History, Check } from 'lucide-react';
import { formatINR } from '@/lib/formatters';

interface CaseProvenanceTraceProps {
  activeCase: OperationalCase;
  onTransitionStage: (id: string, stage: CaseStage) => void;
}

export const CaseProvenanceTrace: React.FC<CaseProvenanceTraceProps> = ({
  activeCase,
  onTransitionStage,
}) => {
  return (
    <AurixCard
      title={`INCIDENT PROVENANCE TRACE / ${activeCase.id}`}
      badge={
        <AurixBadge variant={activeCase.priority === 'CRITICAL' ? 'danger' : 'gold'}>
          {activeCase.stage.replace('_', ' ')}
        </AurixBadge>
      }
    >
      <div className="space-y-6 text-xs font-mono">
        {/* Incident Summary Banner */}
        <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.06] space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-2 pb-2 border-b border-white/[0.04]">
            <div>
              <span className="text-white font-bold text-sm block">{activeCase.title}</span>
              <span className="text-slate-400 text-[10px] mt-0.5 block">
                Target: {activeCase.targetEntityName} ({activeCase.targetEntityId}) • Owner: {activeCase.owner}
              </span>
            </div>
            <div className="text-right">
              <span className="text-[10px] text-slate-500 uppercase block">FINANCIAL AT STAKE</span>
              <span className="text-sm font-bold text-gold">{formatINR(activeCase.exposureINR)}</span>
            </div>
          </div>

          <div>
            <span className="text-[10px] text-gold uppercase font-bold block">ROOT CAUSE ATTRIBUTION</span>
            <p className="text-slate-300 mt-1 leading-relaxed">{activeCase.rootCauseAttribution}</p>
          </div>
        </div>

        {/* Phase 16 Provenance Timeline */}
        <div className="space-y-3">
          <span className="text-[10px] text-slate-500 uppercase tracking-widest font-bold block flex items-center gap-1.5">
            <History className="w-3.5 h-3.5 text-gold" />
            OPERATIONAL LIFECYCLE TRACE (EVENT ➔ DECISION ➔ ACTION)
          </span>

          <div className="relative pl-6 space-y-4 border-l border-white/10 ml-2">
            {activeCase.provenanceLineage.map((step) => (
              <div key={step.stepIndex} className="relative space-y-1">
                <div className="absolute -left-[31px] top-0.5 w-3.5 h-3.5 rounded-full bg-[#07090D] border-2 border-gold" />
                <div className="flex items-center justify-between">
                  <span className="text-white font-bold text-[11px]">{step.title}</span>
                  <span className="text-[10px] text-slate-500">{step.timestamp}</span>
                </div>
                <p className="text-slate-400 text-[10px] leading-relaxed">{step.summary}</p>
                <span className="text-[9px] text-gold/80 block">Actor: {step.actorOrSystem}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Quick Transition Action Bar */}
        <div className="pt-4 border-t border-white/[0.06] flex items-center justify-between">
          <span className="text-slate-500 text-[10px] uppercase">TRANSITION STAGE:</span>
          <div className="flex items-center gap-2">
            {activeCase.stage !== 'INVESTIGATING' && (
              <AurixButton variant="secondary" size="sm" onClick={() => onTransitionStage(activeCase.id, 'INVESTIGATING')}>
                INVESTIGATE
              </AurixButton>
            )}
            {activeCase.stage !== 'AWAITING_APPROVAL' && (
              <AurixButton variant="secondary" size="sm" onClick={() => onTransitionStage(activeCase.id, 'AWAITING_APPROVAL')}>
                SUBMIT FOR APPROVAL
              </AurixButton>
            )}
            {activeCase.stage !== 'RESOLVED' && (
              <AurixButton variant="gold" size="sm" onClick={() => onTransitionStage(activeCase.id, 'RESOLVED')}>
                <Check className="w-3 h-3 mr-1" />
                RESOLVE CASE
              </AurixButton>
            )}
          </div>
        </div>
      </div>
    </AurixCard>
  );
};