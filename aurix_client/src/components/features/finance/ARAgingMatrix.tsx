'use client';

import React from 'react';
import { ARAgingReportDTO } from '@/types/finance.types';
import { AurixCard } from '@/components/ui/AurixCard';
import { AurixBadge } from '@/components/ui/AurixBadge';

export function ARAgingMatrix({ report }: { report: ARAgingReportDTO }) {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <AurixCard title="TOTAL RECEIVABLES" badge={<AurixBadge variant="gold">ACTIVE</AurixBadge>}>
          <div className="text-2xl font-bold font-mono text-white mt-1">
            ${report.totalReceivables.toLocaleString()}
          </div>
          <div className="text-[11px] text-slate-400 mt-1">DSO: {report.dsoDays} Days</div>
        </AurixCard>
        <AurixCard title="TOTAL OVERDUE" badge={<AurixBadge variant="danger">EXPOSURE</AurixBadge>}>
          <div className="text-2xl font-bold font-mono text-[#FF6B6B] mt-1">
            ${report.totalOverdue.toLocaleString()}
          </div>
          <div className="text-[11px] text-slate-400 mt-1">Requires collection action</div>
        </AurixCard>
        <AurixCard title="TOP RISK CUSTOMER" badge={<AurixBadge variant="warning">WATCH</AurixBadge>}>
          <div className="text-sm font-bold font-mono text-white mt-1 truncate">
            {report.topOverdueCustomers[0]?.customerName || 'None'}
          </div>
          <div className="text-[11px] text-[#FF6B6B] mt-1">
            ${report.topOverdueCustomers[0]?.overdueAmount.toLocaleString()} Overdue
          </div>
        </AurixCard>
      </div>

      <AurixCard title="ACCOUNTS RECEIVABLE AGING BRACKETS" badge={<AurixBadge variant="gold">LEDGER AUDITED</AurixBadge>}>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3 pt-2 font-mono text-xs">
          {report.buckets.map((b) => (
            <div key={b.bucket} className="p-3 bg-white/[0.02] rounded-lg border border-white/5 space-y-1">
              <span className="text-slate-400 text-[10px] block uppercase">{b.label}</span>
              <div className="text-white font-bold text-sm">${b.totalAmount.toLocaleString()}</div>
              <div className="text-[10px] text-slate-500">{b.invoicesCount} invoices ({b.percentOfTotal}%)</div>
            </div>
          ))}
        </div>
      </AurixCard>
    </div>
  );
}
