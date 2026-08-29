'use client';

import React from 'react';
import { Target, ShieldCheck } from 'lucide-react';
import { AurixCard } from '@/components/ui/AurixCard';
import { AurixBadge } from '@/components/ui/AurixBadge';
import { AurixButton } from '@/components/ui/AurixButton';

export interface DecisionCardProps {
  id: string;
  title: string;
  domain: string;
  expectedValue: string;
  confidenceScore: number;
  riskLevel: 'LOW' | 'MEDIUM' | 'HIGH';
  preflightStatus: 'PASSED' | 'PENDING' | 'REJECTED';
  rationale: string;
  onExecute?: (id: string) => void;
  onSimulate?: (id: string) => void;
}

export const DecisionCard: React.FC<DecisionCardProps> = ({
  id,
  title,
  domain,
  expectedValue,
  confidenceScore,
  riskLevel,
  preflightStatus,
  rationale,
  onExecute,
  onSimulate,
}) => {
  return (
    <AurixCard
      variant="interactive"
      className="p-5 border-white/[0.08] hover:border-[#D4AF37]/50 space-y-4"
    >
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-white/[0.05] pb-3">
        <div className="flex items-center gap-2">
          <Target className="w-4 h-4 text-[#D4AF37]" />
          <span className="text-[10px] font-mono text-slate-500 uppercase">{domain} • {id}</span>
        </div>
        <div className="flex items-center gap-2">
          <AurixBadge variant={riskLevel === 'HIGH' ? 'danger' : riskLevel === 'MEDIUM' ? 'warning' : 'success'}>
            RISK: {riskLevel}
          </AurixBadge>
          <AurixBadge variant="gold">
            CONF: {confidenceScore}%
          </AurixBadge>
        </div>
      </div>

      <div>
        <h4 className="text-sm font-bold text-white uppercase font-mono tracking-wide">
          {title}
        </h4>
        <p className="text-xs text-slate-400 font-sans mt-1 leading-relaxed">
          {rationale}
        </p>
      </div>

      <div className="grid grid-cols-2 gap-3 py-2 px-3 rounded-lg bg-white/[0.02] border border-white/[0.04] font-mono text-xs">
        <div>
          <span className="text-[9px] text-slate-500 uppercase block">EXPECTED VALUE (EV)</span>
          <span className="text-base font-extrabold text-[#3DDB91]">{expectedValue}</span>
        </div>
        <div className="flex items-center justify-end gap-1.5">
          <ShieldCheck className="w-4 h-4 text-[#3DDB91]" />
          <span className="text-[10px] font-bold text-white uppercase">PREFLIGHT: {preflightStatus}</span>
        </div>
      </div>

      <div className="flex items-center justify-end gap-3 pt-2">
        {onSimulate && (
          <AurixButton variant="glass" size="sm" onClick={() => onSimulate(id)}>
            SIMULATE TWIN
          </AurixButton>
        )}
        {onExecute && (
          <AurixButton variant="gold" size="sm" onClick={() => onExecute(id)}>
            EXECUTE ACTION
          </AurixButton>
        )}
      </div>
    </AurixCard>
  );
};
