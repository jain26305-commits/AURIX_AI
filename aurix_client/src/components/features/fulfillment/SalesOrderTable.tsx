'use client';

import React from 'react';
import { SalesOrderItem } from '@/types/fulfillment.types';
import { AurixBadge } from '@/components/ui/AurixBadge';
import { formatINR } from '@/lib/formatters';

interface SalesOrderTableProps {
  orders: SalesOrderItem[];
}

export const SalesOrderTable: React.FC<SalesOrderTableProps> = ({ orders }) => {
  return (
    <div className="w-full aurix-card-glass rounded-xl p-6 border border-white/[0.08] select-none font-mono">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="border-b border-white/[0.08] text-slate-500 text-[10px] uppercase tracking-wider">
              <th className="pb-3 pl-2">Order ID & Customer</th>
              <th className="pb-3">Channel</th>
              <th className="pb-3">Target SKU</th>
              <th className="pb-3">Ordered / Allocated</th>
              <th className="pb-3">Promised Date</th>
              <th className="pb-3">Order Value</th>
              <th className="pb-3 text-right pr-2">Allocation Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/[0.04]">
            {orders.map((ord) => {
              const isAllocated = ord.status === 'ALLOCATED';
              const isBackordered = ord.status === 'BACKORDERED';
              const isPartial = ord.status === 'PARTIALLY_ALLOCATED';

              return (
                <tr key={ord.orderId} className="hover:bg-white/[0.02] transition-colors">
                  <td className="py-3.5 pl-2">
                    <div className="flex flex-col">
                      <span className="text-white font-bold text-xs">{ord.orderId}</span>
                      <span className="text-slate-400 text-[10px]">{ord.customerName}</span>
                    </div>
                  </td>

                  <td className="py-3.5">
                    <AurixBadge variant={ord.channel === 'E-COMMERCE' ? 'info' : ord.channel === 'B2B_WHOLESALE' ? 'gold' : 'neutral'}>
                      {ord.channel.replace('_', ' ')}
                    </AurixBadge>
                  </td>

                  <td className="py-3.5">
                    <span className="text-white font-bold block">{ord.skuName}</span>
                    <span className="text-slate-500 text-[10px]">{ord.skuId}</span>
                  </td>

                  <td className="py-3.5">
                    <span className="text-white font-bold block">
                      {ord.allocatedUnits} / {ord.orderedUnits} pcs
                    </span>
                    <div className="w-24 h-1.5 bg-white/5 rounded-full overflow-hidden mt-1">
                      <div
                        className={`h-full rounded-full ${
                          isAllocated ? 'bg-[#3DDB91]' : isPartial ? 'bg-[#F3B33D]' : 'bg-[#FF6B6B]'
                        }`}
                        style={{ width: `${ord.allocationPercent}%` }}
                      />
                    </div>
                  </td>

                  <td className="py-3.5 text-slate-300">{ord.promisedDate}</td>

                  <td className="py-3.5 text-gold font-bold">{formatINR(ord.totalAmountINR)}</td>

                  <td className="py-3.5 text-right pr-2">
                    <AurixBadge
                      variant={isAllocated ? 'success' : isPartial ? 'warning' : isBackordered ? 'danger' : 'neutral'}
                      pulse={isBackordered}
                    >
                      {ord.status.replace('_', ' ')}
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