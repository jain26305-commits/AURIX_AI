'use client';

import React from 'react';
import { APAgingReportDTO } from '@/types/finance.types';
import { AurixCard } from '@/components/ui/AurixCard';
import { AurixBadge } from '@/components/ui/AurixBadge';

export function APAgingMatrix({ report }: { report: APAgingReportDTO }) {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <AurixCard title="TOTAL PAYABLES" badge={<AurixBadge variant="gold">AP BUFFER</AurixBadge>}>
          <div className="text-2xl font-bold font-mono text-white mt-1">
            ${report.totalPayables.toLocaleString()}
          </div>
          <div className="text-[11px] text-slate-400 mt-1">DPO: {report.dpoDays} Days</div>
        </AurixCard>
        <AurixCard title="OVERDUE PAYABLES" badge={<AurixBadge variant="warning">PENDING</AurixBadge>}>
          <div className="text-2xl font-bold font-mono text-[#F3B33D] mt-1">
            ${report.totalOverdue.toLocaleString()}
          </div>
          <div className="text-[11px] text-slate-400 mt-1">Scheduled for clearance</div>
        </AurixCard>
        <AurixCard title="UPCOMING DISBURSEMENT" badge={<AurixBadge variant="success">DISCOUNT</AurixBadge>}>
          <div className="text-sm font-bold font-mono text-white mt-1 truncate">
            {report.upcomingDisbursements[0]?.supplierName || 'None'}
          </div>
          <div className="text-[11px] text-[#3DDB91] mt-1">
            ${report.upcomingDisbursements[0]?.amount.toLocaleString()} Due Soon
          </div>
        </AurixCard>
      </div>

      <AurixCard title="ACCOUNTS PAYABLE AGING BRACKETS" badge={<AurixBadge variant="gold">DISBURSEMENT AUDIT</AurixBadge>}>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3 pt-2 font-mono text-xs">
          {report.buckets.map((b) => (
            <div key={b.bucket} className="p-3 bg-white/[0.02] rounded-lg border border-white/5 space-y-1">
              <span className="text-slate-400 text-[10px] block uppercase">{b.label}</span>
              <div className="text-white font-bold text-sm">${b.totalAmount.toLocaleString()}</div>
              <div className="text-[10px] text-slate-500">{b.invoicesCount} invoices</div>
            </div>
          ))}
        </div>
      </AurixCard>
    </div>
  );
}
