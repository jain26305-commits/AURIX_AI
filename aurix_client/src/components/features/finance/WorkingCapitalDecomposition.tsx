'use client';

import React from 'react';
import { WorkingCapitalDTO } from '@/types/finance.types';
import { AurixCard } from '@/components/ui/AurixCard';
import { AurixBadge } from '@/components/ui/AurixBadge';

export function WorkingCapitalDecomposition({ data }: { data: WorkingCapitalDTO }) {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 font-mono">
        <AurixCard title="CASH CONVERSION CYCLE" badge={<AurixBadge variant="gold">{data.cashConversionCycleDays} DAYS</AurixBadge>}>
          <div className="text-2xl font-bold text-white mt-1">{data.cashConversionCycleDays} Days</div>
          <div className="text-[11px] text-slate-400 mt-1">DSO + DIO - DPO</div>
        </AurixCard>
        <AurixCard title="DAYS SALES OUTSTANDING" badge={<AurixBadge variant="warning">{data.dsoDays} DAYS</AurixBadge>}>
          <div className="text-2xl font-bold text-white mt-1">{data.dsoDays} Days</div>
          <div className="text-[11px] text-slate-400 mt-1">${data.accountsReceivable.toLocaleString()} AR</div>
        </AurixCard>
        <AurixCard title="DAYS INVENTORY OUT" badge={<AurixBadge variant="gold">{data.dioDays} DAYS</AurixBadge>}>
          <div className="text-2xl font-bold text-white mt-1">{data.dioDays} Days</div>
          <div className="text-[11px] text-slate-400 mt-1">${data.inventoryValuation.toLocaleString()} Inventory</div>
        </AurixCard>
        <AurixCard title="DAYS PAYABLES OUT" badge={<AurixBadge variant="success">{data.dpoDays} DAYS</AurixBadge>}>
          <div className="text-2xl font-bold text-white mt-1">{data.dpoDays} Days</div>
          <div className="text-[11px] text-slate-400 mt-1">${data.accountsPayable.toLocaleString()} AP</div>
        </AurixCard>
      </div>

      <AurixCard title="WORKING CAPITAL DRIVERS & IMPACT" badge={<AurixBadge variant="gold">OPERATIONAL VELOCITY</AurixBadge>}>
        <div className="space-y-3 pt-2 font-mono text-xs">
          {data.drivers.map((d, i) => (
            <div key={i} className="p-3 rounded-lg bg-white/[0.02] border border-white/[0.05] flex items-center justify-between">
              <div>
                <span className="text-white font-bold block">{d.driver}</span>
                <span className="text-[10px] text-slate-400">Capital Impact: ${Math.abs(d.capitalImpact).toLocaleString()}</span>
              </div>
              <AurixBadge variant={d.direction === 'FAVORABLE' ? 'success' : 'danger'}>
                {d.impactDays > 0 ? `+${d.impactDays}d` : `${d.impactDays}d`} {d.direction}
              </AurixBadge>
            </div>
          ))}
        </div>
      </AurixCard>
    </div>
  );
}
