'use client';

import React from 'react';
import { ReturnsSummary } from '@/types/returns.types';
import { AurixCard } from '@/components/ui/AurixCard';
import { AurixBadge } from '@/components/ui/AurixBadge';
import { RotateCcw, DollarSign, ShieldAlert, CheckCircle2 } from 'lucide-react';
import { formatINR } from '@/lib/formatters';

export const ReturnsStatsBar: React.FC<{ summary: ReturnsSummary }> = ({ summary }) => {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 select-none font-mono">
      <AurixCard title="TOTAL RETURN RATE" badge={<AurixBadge variant="info">PORTFOLIO</AurixBadge>}>
        <div className="flex items-baseline justify-between mt-2">
          <span className="text-2xl font-bold text-white">{summary.portfolioReturnRatePercent}%</span>
          <RotateCcw className="w-5 h-5 text-[#D4AF37]" />
        </div>
        <div className="text-[11px] text-slate-400 mt-1">{summary.totalReturnedUnits} returned units across 0{summary.totalReturnsCount} RMAs</div>
      </AurixCard>

      <AurixCard title="AGGREGATE REFUNDS" badge={<AurixBadge variant="warning">OUTFLOW</AurixBadge>}>
        <div className="flex items-baseline justify-between mt-2">
          <span className="text-2xl font-bold text-[#F3B33D]">{formatINR(summary.aggregateRefundINR)}</span>
          <DollarSign className="w-5 h-5 text-[#F3B33D]" />
        </div>
        <div className="text-[11px] text-slate-400 mt-1">Processed customer refunds</div>
      </AurixCard>

      <AurixCard title="NET FINANCIAL LOSS" badge={<AurixBadge variant="danger" pulse>UNRECOVERABLE</AurixBadge>}>
        <div className="flex items-baseline justify-between mt-2">
          <span className="text-2xl font-bold text-[#FF6B6B]">{formatINR(summary.netLossINR)}</span>
          <ShieldAlert className="w-5 h-5 text-[#FF6B6B]" />
        </div>
        <div className="text-[11px] text-slate-400 mt-1">Scrap & rework labor losses</div>
      </AurixCard>

      <AurixCard title="PRIMARY RETURN REASON" badge={<AurixBadge variant="gold">ROOT CAUSE</AurixBadge>}>
        <div className="flex items-baseline justify-between mt-2">
          <span className="text-2xl font-bold text-gold">{summary.topReturnReason.replace('_', ' ')}</span>
          <CheckCircle2 className="w-5 h-5 text-gold" />
        </div>
        <div className="text-[11px] text-slate-400 mt-1">66.7% restored to prime A-grade inventory</div>
      </AurixCard>
    </div>
  );
};