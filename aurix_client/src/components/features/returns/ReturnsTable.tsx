'use client';

import React from 'react';
import { ReturnRecord } from '@/types/returns.types';
import { AurixBadge } from '@/components/ui/AurixBadge';
import { formatINR } from '@/lib/formatters';

interface ReturnsTableProps {
  returns: ReturnRecord[];
}

export const ReturnsTable: React.FC<ReturnsTableProps> = ({ returns }) => {
  return (
    <div className="w-full aurix-card-glass rounded-xl p-6 border border-white/[0.08] select-none font-mono">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="border-b border-white/[0.08] text-slate-500 text-[10px] uppercase tracking-wider">
              <th className="pb-3 pl-2">RMA & Order ID</th>
              <th className="pb-3">Customer & Material</th>
              <th className="pb-3">Return Reason</th>
              <th className="pb-3">Qty</th>
              <th className="pb-3">Refund Amount</th>
              <th className="pb-3">Net Loss</th>
              <th className="pb-3 text-right pr-2">Disposition Route</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/[0.04]">
            {returns.map((r) => {
              const isRestock = r.disposition === 'RESTOCK';
              const isScrap = r.disposition === 'SCRAP';
              const isRework = r.disposition === 'REWORK';

              return (
                <tr key={r.rmaNumber} className="hover:bg-white/[0.02] transition-colors">
                  <td className="py-3.5 pl-2">
                    <span className="text-white font-bold text-xs block">{r.rmaNumber}</span>
                    <span className="text-gold text-[10px]">{r.orderId}</span>
                  </td>

                  <td className="py-3.5">
                    <span className="text-white font-bold block">{r.customerName}</span>
                    <span className="text-slate-400 text-[10px]">{r.skuName} ({r.skuId})</span>
                  </td>

                  <td className="py-3.5">
                    <span className="text-slate-300 font-medium">{r.returnReason.replace('_', ' ')}</span>
                  </td>

                  <td className="py-3.5 text-white font-bold">{r.returnQty} pcs</td>

                  <td className="py-3.5 text-slate-300">{formatINR(r.refundAmountINR)}</td>

                  <td className="py-3.5">
                    <span className={r.netFinancialLossINR > 0 ? 'text-[#FF8585] font-bold' : 'text-[#3DDB91]'}>
                      {r.netFinancialLossINR > 0 ? formatINR(r.netFinancialLossINR) : '₹0 (Recovered)'}
                    </span>
                  </td>

                  <td className="py-3.5 text-right pr-2">
                    <AurixBadge variant={isRestock ? 'success' : isRework ? 'warning' : isScrap ? 'danger' : 'neutral'}>
                      {r.disposition}
                    </AurixBadge>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};