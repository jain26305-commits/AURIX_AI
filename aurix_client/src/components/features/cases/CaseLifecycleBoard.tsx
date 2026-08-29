'use client';

import React from 'react';
import { CaseStage, OperationalCase } from '@/types/case.types';
import { AurixBadge } from '@/components/ui/AurixBadge';
import { formatINR } from '@/lib/formatters';

const STAGES: CaseStage[] = [
  'OPEN',
  'INVESTIGATING',
  'AWAITING_DECISION',
  'AWAITING_APPROVAL',
  'RESOLVED',
];

interface CaseLifecycleBoardProps {
  cases: OperationalCase[];
  selectedCaseId: string | null;
  onSelectCase: (id: string) => void;
  onTransitionStage: (id: string, stage: CaseStage) => void;
}

export const CaseLifecycleBoard: React.FC<CaseLifecycleBoardProps> = ({
  cases,
  selectedCaseId,
  onSelectCase,
  onTransitionStage,
}) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-5 gap-3 text-xs font-mono select-none">
      {STAGES.map((stage) => {
        const casesInStage = cases.filter((c) => c.stage === stage);

        return (
          <div
            key={stage}
            className="aurix-card-glass rounded-xl p-3.5 border border-white/[0.08] flex flex-col space-y-3 min-h-[22rem]"
          >
            <div className="flex items-center justify-between pb-2 border-b border-white/[0.06]">
              <span className="font-bold text-[10px] tracking-wider text-white uppercase">
                {stage.replace('_', ' ')}
              </span>

              <AurixBadge variant="neutral">
                {casesInStage.length}
              </AurixBadge>
            </div>

            <div className="space-y-2.5 flex-1 overflow-y-auto">
              {casesInStage.map((caseItem) => {
                const isSelected = caseItem.id === selectedCaseId;
                const isCritical = caseItem.priority === 'CRITICAL';

                return (
                  <div
                    key={caseItem.id}
                    onClick={() => onSelectCase(caseItem.id)}
                    className={`p-3 rounded-lg border cursor-pointer transition-all duration-150 space-y-2 ${
                      isSelected
                        ? 'bg-gold/[0.08] border-gold/40 shadow-[0_0_15px_rgba(212,175,55,0.15)]'
                        : isCritical
                          ? 'bg-[#FF6B6B]/[0.03] border-[#FF6B6B]/30 hover:border-[#FF6B6B]/60'
                          : 'bg-white/[0.02] border-white/[0.06] hover:border-white/20'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-[9px] text-slate-500 font-bold">
                        {caseItem.id}
                      </span>

                      <AurixBadge
                        variant={
                          isCritical
                            ? 'danger'
                            : caseItem.priority === 'HIGH'
                              ? 'warning'
                              : 'info'
                        }
                      >
                        {caseItem.priority}
                      </AurixBadge>
                    </div>

                    <h4
                      className={`text-xs font-bold leading-snug line-clamp-2 ${
                        isSelected ? 'text-gold' : 'text-white'
                      }`}
                    >
                      {caseItem.title}
                    </h4>

                    <div className="pt-1.5 border-t border-white/[0.04] flex items-center justify-between text-[10px] text-slate-400">
                      <span>{caseItem.targetEntityId}</span>

                      <span className="text-white font-bold">
                        {formatINR(caseItem.exposureINR)}
                      </span>
                    </div>

                    <div
                      className="pt-2"
                      onClick={(event) => event.stopPropagation()}
                    >
                      <select
                        value={caseItem.stage}
                        onChange={(event) =>
                          onTransitionStage(
                            caseItem.id,
                            event.target.value as CaseStage
                          )
                        }
                        className="w-full bg-black/40 border border-white/10 rounded-md px-2 py-1.5 text-[9px] text-slate-300 uppercase tracking-wide focus:outline-none focus:border-[#D4AF37]/50"
                        aria-label={`Change stage for ${caseItem.id}`}
                      >
                        {STAGES.map((availableStage) => (
                          <option
                            key={availableStage}
                            value={availableStage}
                          >
                            {availableStage.replace('_', ' ')}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        );
      })}
    </div>
  );
};