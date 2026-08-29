'use client';

import React from 'react';
import { AlertFeedSummary } from '@/types/alert.types';
import { AurixCard } from '@/components/ui/AurixCard';
import { AurixBadge } from '@/components/ui/AurixBadge';
import { AlertOctagon, AlertTriangle, ShieldCheck, DollarSign } from 'lucide-react';
import { formatINR } from '@/lib/formatters';

export const AlertStatsBar: React.FC<{ summary: AlertFeedSummary }> = ({ summary }) => {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 select-none">
      <AurixCard title="CRITICAL BREACHES" badge={<AurixBadge variant="danger" pulse>ACTION REQUIRED</AurixBadge>}>
        <div className="flex items-baseline justify-between mt-2">
          <span className="text-2xl font-bold font-mono text-[#FF6B6B]">0{summary.criticalCount}</span>
          <AlertOctagon className="w-5 h-5 text-[#FF6B6B]" />
        </div>
        <div className="text-[11px] font-mono text-slate-400 mt-1">Breach horizon &lt;= 7 days</div>
      </AurixCard>

      <AurixCard title="WARNING WATCHLIST" badge={<AurixBadge variant="warning">WATCH</AurixBadge>}>
        <div className="flex items-baseline justify-between mt-2">
          <span className="text-2xl font-bold font-mono text-[#F3B33D]">0{summary.warningCount}</span>
          <AlertTriangle className="w-5 h-5 text-[#F3B33D]" />
        </div>
        <div className="text-[11px] font-mono text-slate-400 mt-1">Capacity & lead-time drag</div>
      </AurixCard>

      <AurixCard title="FINANCIAL AT RISK" badge={<AurixBadge variant="gold">EXPOSURE</AurixBadge>}>
        <div className="flex items-baseline justify-between mt-2">
          <span className="text-2xl font-bold font-mono text-gold">{formatINR(summary.totalFinancialExposureINR)}</span>
          <DollarSign className="w-5 h-5 text-gold" />
        </div>
        <div className="text-[11px] font-mono text-slate-400 mt-1">Gross revenue at stake</div>
      </AurixCard>

      <AurixCard title="TRIAGE STATUS" badge={<AurixBadge variant="info">UNACKNOWLEDGED</AurixBadge>}>
        <div className="flex items-baseline justify-between mt-2">
          <span className="text-2xl font-bold font-mono text-white">0{summary.unacknowledgedCount}</span>
          <ShieldCheck className="w-5 h-5 text-[#D4AF37]" />
        </div>
        <div className="text-[11px] font-mono text-slate-400 mt-1">Awaiting operator acknowledgement</div>
      </AurixCard>
    </div>
  );
};