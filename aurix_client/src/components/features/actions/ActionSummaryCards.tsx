'use client';

import React from 'react';
import { ActionCenterSummary } from '@/types/action.types';
import { AurixCard } from '@/components/ui/AurixCard';
import { AurixBadge } from '@/components/ui/AurixBadge';
import { ShieldCheck, Zap, DollarSign, CheckCircle2 } from 'lucide-react';
import { formatINR } from '@/lib/formatters';

export const ActionSummaryCards: React.FC<{ summary: ActionCenterSummary }> = ({ summary }) => {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 select-none font-mono">
      <AurixCard title="AWAITING APPROVAL" badge={<AurixBadge variant="warning">SIGN-OFF REQUIRED</AurixBadge>}>
        <div className="flex items-baseline justify-between mt-2">
          <span className="text-2xl font-bold text-[#F3B33D]">0{summary.awaitingApprovalCount}</span>
          <Zap className="w-5 h-5 text-[#F3B33D]" />
        </div>
        <div className="text-[11px] text-slate-400 mt-1">Preflight validated & queued</div>
      </AurixCard>

      <AurixCard title="APPROVED & READY" badge={<AurixBadge variant="gold">PHASE 14 QUEUE</AurixBadge>}>
        <div className="flex items-baseline justify-between mt-2">
          <span className="text-2xl font-bold text-gold">0{summary.executedTodayCount + 1}</span>
          <ShieldCheck className="w-5 h-5 text-gold" />
        </div>
        <div className="text-[11px] text-slate-400 mt-1">Cryptographically authorized</div>
      </AurixCard>

      <AurixCard title="COMMITTED CAPITAL" badge={<AurixBadge variant="info">OUTFLOW</AurixBadge>}>
        <div className="flex items-baseline justify-between mt-2">
          <span className="text-2xl font-bold text-white">{formatINR(summary.totalCommittedCapitalINR)}</span>
          <DollarSign className="w-5 h-5 text-[#D4AF37]" />
        </div>
        <div className="text-[11px] text-slate-400 mt-1">Execution cost across active batch</div>
      </AurixCard>

      <AurixCard title="EXPOSURE AVERTED" badge={<AurixBadge variant="success">NET ROI GAIN</AurixBadge>}>
        <div className="flex items-baseline justify-between mt-2">
          <span className="text-2xl font-bold text-[#3DDB91]">{formatINR(summary.totalProtectedExposureINR)}</span>
          <CheckCircle2 className="w-5 h-5 text-[#3DDB91]" />
        </div>
        <div className="text-[11px] text-slate-400 mt-1">Gross operational risk averted</div>
      </AurixCard>
    </div>
  );
};