'use client';

import React from 'react';
import { MrpItemPlan } from '@/types/manufacturing.types';


import { Calendar } from 'lucide-react';

interface MrpScheduleTableProps {
  plan: MrpItemPlan;
  availablePlans?: any[];
  selectedSkuId: string;
  onSelectSku: (skuId: string) => void;
}

export const MrpScheduleTable: React.FC<MrpScheduleTableProps> = ({
  plan,
  availablePlans,
  selectedSkuId,
  onSelectSku,
}) => {
  return (
    <div className="w-full aurix-card-glass rounded-xl p-6 border border-white/[0.08] select-none font-mono space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-white/[0.06]">
        <div>
          <div className="flex items-center gap-2">
            <Calendar className="w-4 h-4 text-[#D4AF37]" />
            <h3 className="text-sm font-bold text-white tracking-wide">
              TIME-PHASED MATERIAL REQUIREMENTS PLANNING (MRP) / {plan.skuId}
            </h3>
          </div>
          <span className="text-slate-400 text-[11px] mt-0.5 block">
            Lot Sizing: <span className="text-gold font-bold">{plan.lotSizeRule}</span> • Lead Time: {plan.leadTimeDays}d • Safety Stock: {plan.safetyStockUnits}u • Starting On-Hand: {plan.startingOnHand}u
          </span>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-[10px] text-slate-500 uppercase">PLANNING ITEM:</span>
          <select
            value={selectedSkuId}
            onChange={(e) => onSelectSku(e.target.value)}
            className="bg-[#15171A] border border-white/15 rounded-lg px-3 py-1.5 text-slate-200 font-mono text-xs focus:outline-none focus:border-[#D4AF37]"
          >
            {(availablePlans || []).map((p) => (
              <option key={p.skuId} value={p.skuId}>
                {p.skuId} — {p.skuName}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-center text-xs">
          <thead>
            <tr className="border-b border-white/[0.08] text-slate-500 text-[10px] uppercase tracking-wider">
              <th className="pb-3 text-left pl-2">MRP Planning Parameter</th>
              {(plan.timeBuckets || []).map((b: any) => (
                <th key={b.periodLabel} className="pb-3 px-3">{b.periodLabel}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-white/[0.04]">
            <tr>
              <td className="py-3 text-left pl-2 text-slate-300 font-medium">Gross Requirements</td>
              {(plan.timeBuckets || []).map((b: any, idx: any) => (
                <td key={idx} className="py-3 text-white font-bold">{b.grossRequirements}</td>
              ))}
            </tr>

            <tr>
              <td className="py-3 text-left pl-2 text-slate-400">Scheduled Receipts</td>
              {(plan.timeBuckets || []).map((b: any, idx: any) => (
                <td key={idx} className="py-3 text-[#D4AF37]">{b.scheduledReceipts || '—'}</td>
              ))}
            </tr>

            <tr className="bg-white/[0.02]">
              <td className="py-3 text-left pl-2 font-bold text-slate-200">Projected Available Balance (PAB)</td>
              {(plan.timeBuckets || []).map((b: any, idx: any) => (
                <td key={idx} className={`py-3 font-bold ${b.projectedAvailableBalance < plan.safetyStockUnits ? 'text-[#FF8585]' : 'text-[#3DDB91]'}`}>
                  {b.projectedAvailableBalance}
                </td>
              ))}
            </tr>

            <tr>
              <td className="py-3 text-left pl-2 text-[#F3B33D] font-medium">Net Requirements</td>
              {(plan.timeBuckets || []).map((b: any, idx: any) => (
                <td key={idx} className="py-3 text-[#F3B33D] font-bold">{b.netRequirements || '—'}</td>
              ))}
            </tr>

            <tr>
              <td className="py-3 text-left pl-2 text-slate-400">Planned Order Receipts</td>
              {(plan.timeBuckets || []).map((b: any, idx: any) => (
                <td key={idx} className="py-3 text-white">{b.plannedOrderReceipts || '—'}</td>
              ))}
            </tr>

            <tr className="bg-gold/[0.04]">
              <td className="py-3 text-left pl-2 text-gold font-bold">Planned Order Releases</td>
              {(plan.timeBuckets || []).map((b: any, idx: any) => (
                <td key={idx} className="py-3 text-gold font-bold">{b.plannedOrderReleases || '—'}</td>
              ))}
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
};