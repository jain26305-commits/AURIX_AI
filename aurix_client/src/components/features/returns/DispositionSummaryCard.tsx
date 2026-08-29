'use client';

import React from 'react';
import { DispositionMetric } from '@/types/returns.types';
import { AurixBadge } from '@/components/ui/AurixBadge';
import { Recycle } from 'lucide-react';
import { formatINR } from '@/lib/formatters';

interface DispositionSummaryCardProps {
  metrics: DispositionMetric[];
}

export const DispositionSummaryCard: React.FC<DispositionSummaryCardProps> = ({ metrics }) => {
  return (
    <div className="w-full aurix-card-glass rounded-xl p-6 border border-white/[0.08] select-none font-mono space-y-6">
      <div className="flex items-center justify-between pb-4 border-b border-white/[0.06]">
        <div>
          <h3 className="text-sm font-bold text-white tracking-wide flex items-center gap-2">
            <Recycle className="w-4 h-4 text-gold" />
            REVERSE LOGISTICS DISPOSITION & SALVAGE RECOVERY
          </h3>
          <p className="text-[11px] text-slate-400 mt-0.5">
            Physical routing breakdown and salvage value recovery across returned units.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {metrics.map((m) => (
          <div key={m.disposition} className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.06] space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-white font-bold text-xs">{m.disposition}</span>
              <AurixBadge variant={m.disposition === 'RESTOCK' ? 'success' : m.disposition === 'REWORK' ? 'warning' : 'danger'}>
                {m.percentageOfTotal}%
              </AurixBadge>
            </div>

            <div className="space-y-1">
              <span className="text-2xl font-bold text-white font-mono">{m.unitsCount} pcs</span>
              <div className="flex justify-between text-[10px] text-slate-400 pt-2 border-t border-white/[0.04]">
                <span>Total Refund: {formatINR(m.totalRefundINR)}</span>
                <span className="text-[#3DDB91] font-bold">Salvage: {formatINR(m.salvageRecoveryINR)}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};