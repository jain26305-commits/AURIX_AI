'use client';

import React from 'react';
import { ScenarioOutcomeDelta } from '@/types/scenario.types';
import { AurixCard } from '@/components/ui/AurixCard';
import { AurixBadge } from '@/components/ui/AurixBadge';


interface PolicyImpactSummaryProps {
  scenario: ScenarioOutcomeDelta;
}

export const PolicyImpactSummary: React.FC<PolicyImpactSummaryProps> = ({ scenario }) => {
  return (
    <AurixCard
      title="EXECUTIVE STRATEGIC RATIONALE"
      badge={
        scenario.isRecommended ? (
          <AurixBadge variant="gold">AURIX CHAMPION STRATEGY</AurixBadge>
        ) : (
          <AurixBadge variant="neutral">SIMULATION EVALUATION</AurixBadge>
        )
      }
    >
      <div className="space-y-4 text-xs font-mono">
        <div className="flex items-center justify-between pb-3 border-b border-white/[0.06]">
          <span className="text-white font-bold text-sm">{scenario.name}</span>
          <span className="text-gold font-bold uppercase">{scenario.branchType}</span>
        </div>

        <p className="text-slate-300 leading-relaxed bg-white/[0.02] p-4 rounded-xl border border-white/[0.04]">
          {scenario.strategicRationale}
        </p>

        <div className="grid grid-cols-3 gap-3 pt-2 text-center">
          <div className="p-3 rounded-lg bg-white/[0.02] border border-white/[0.06]">
            <span className="text-[10px] text-slate-500 uppercase block">PROJECTED SERVICE</span>
            <span className="text-base font-bold text-[#3DDB91] mt-0.5 block">{scenario.projectedServiceLevelPercent}%</span>
          </div>
          <div className="p-3 rounded-lg bg-white/[0.02] border border-white/[0.06]">
            <span className="text-[10px] text-slate-500 uppercase block">CAPITAL IMPACT</span>
            <span className="text-base font-bold text-white mt-0.5 block">
              {(scenario?.workingCapitalDeltaINR || 0) >= 0 ? `+₹${((scenario?.workingCapitalDeltaINR || 0) / 1000).toFixed(0)}k` : `-₹${(Math.abs((scenario?.workingCapitalDeltaINR || 0)) / 1000).toFixed(0)}k`}
            </span>
          </div>
          <div className="p-3 rounded-lg bg-gold/10 border border-gold/30">
            <span className="text-[10px] text-gold uppercase block font-bold">NET CASH DELTA</span>
            <span className="text-base font-bold text-gold mt-0.5 block">
              {scenario.netFinancialImpactINR >= 0 ? `+₹${(scenario.netFinancialImpactINR / 1000).toFixed(0)}k` : `-₹${(Math.abs(scenario.netFinancialImpactINR) / 1000).toFixed(0)}k`}
            </span>
          </div>
        </div>
      </div>
    </AurixCard>
  );
};