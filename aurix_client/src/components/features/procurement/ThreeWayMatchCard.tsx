'use client';

import React from 'react';
import { ThreeWayMatchRecord } from '@/types/procurement.types';
import { AurixBadge } from '@/components/ui/AurixBadge';
import { formatINR } from '@/lib/formatters';

interface ThreeWayMatchCardProps {
  matches: ThreeWayMatchRecord[];
}

export const ThreeWayMatchCard: React.FC<ThreeWayMatchCardProps> = ({ matches }) => {
  return (
    <div className="w-full aurix-card-glass rounded-xl p-6 border border-white/[0.08] select-none font-mono">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="border-b border-white/[0.08] text-slate-500 text-[10px] uppercase tracking-wider">
              <th className="pb-3 pl-2">Audit ID & PO</th>
              <th className="pb-3">Vendor & Invoice</th>
              <th className="pb-3">PO Amount</th>
              <th className="pb-3">GRN Received</th>
              <th className="pb-3">Invoice Amount</th>
              <th className="pb-3">Audit Variance</th>
              <th className="pb-3 text-right pr-2">Reconciliation Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/[0.04]">
            {matches.map((m) => {
              const isMatched = m.status === 'MATCHED';
              const isDiscrepancy = m.status.startsWith('DISCREPANCY');

              return (
                <tr key={m.matchId} className="hover:bg-white/[0.02] transition-colors">
                  <td className="py-3.5 pl-2">
                    <span className="text-slate-500 text-[10px] block font-bold">{m.matchId}</span>
                    <span className="text-white font-bold text-xs">{m.poNumber}</span>
                  </td>

                  <td className="py-3.5">
                    <span className="text-white font-bold block">{m.vendorName}</span>
                    <span className="text-[10px] text-gold">{m.invoiceNumber}</span>
                  </td>

                  <td className="py-3.5 text-slate-300">{formatINR(m.poAmountINR)}</td>
                  <td className="py-3.5 text-slate-300">{formatINR(m.grnAmountINR)}</td>
                  <td className="py-3.5 text-slate-300">{formatINR(m.invoiceAmountINR)}</td>

                  <td className="py-3.5">
                    <span className={m.varianceINR !== 0 ? 'text-[#FF8585] font-bold' : 'text-[#3DDB91] font-bold'}>
                      {m.varianceINR === 0 ? '₹0' : formatINR(m.varianceINR)}
                    </span>
                    {m.discrepancyNote && (
                      <span className="text-[10px] text-slate-400 block mt-0.5 max-w-xs truncate" title={m.discrepancyNote}>
                        {m.discrepancyNote}
                      </span>
                    )}
                  </td>

                  <td className="py-3.5 text-right pr-2">
                    <AurixBadge
                      variant={isMatched ? 'success' : isDiscrepancy ? 'danger' : 'warning'}
                      pulse={isDiscrepancy}
                    >
                      {m.status.replace('_', ' ')}
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