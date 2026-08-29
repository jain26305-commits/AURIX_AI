'use client';

import React from 'react';
import { PurchaseOrder } from '@/types/procurement.types';
import { AurixBadge } from '@/components/ui/AurixBadge';
import { formatINR } from '@/lib/formatters';

interface PurchaseOrderTableProps {
  orders: PurchaseOrder[];
}

export const PurchaseOrderTable: React.FC<PurchaseOrderTableProps> = ({ orders }) => {
  return (
    <div className="w-full aurix-card-glass rounded-xl p-6 border border-white/[0.08] select-none font-mono">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="border-b border-white/[0.08] text-slate-500 text-[10px] uppercase tracking-wider">
              <th className="pb-3 pl-2">PO Number & Vendor</th>
              <th className="pb-3">Order Date</th>
              <th className="pb-3">Promised Delivery</th>
              <th className="pb-3">Line Items</th>
              <th className="pb-3">Total Value</th>
              <th className="pb-3">Tracking / ASN</th>
              <th className="pb-3 text-right pr-2">Lifecycle State</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/[0.04]">
            {orders.map((po) => {
              const isDelayed = po.revisedEtaDate && po.revisedEtaDate > po.promisedDeliveryDate;
              const isReceived = po.status === 'RECEIVED' || po.status === 'RECONCILED';
              const isInTransit = po.status === 'IN_TRANSIT';

              return (
                <tr key={po.poNumber} className="hover:bg-white/[0.02] transition-colors">
                  <td className="py-3.5 pl-2">
                    <div className="flex flex-col">
                      <span className="text-white font-bold text-xs">{po.poNumber}</span>
                      <span className="text-[10px] text-gold mt-0.5">{po.vendorName}</span>
                    </div>
                  </td>

                  <td className="py-3.5 text-slate-400">{po.orderDate}</td>

                  <td className="py-3.5">
                    <span className="text-slate-200 block">{po.promisedDeliveryDate}</span>
                    {isDelayed && (
                      <span className="text-[#FF8585] text-[10px] block font-bold">
                        ETA: {po.revisedEtaDate} (Late)
                      </span>
                    )}
                  </td>

                  <td className="py-3.5">
                    <span className="text-white font-bold block">{po.lineItems.length} Materials</span>
                    <span className="text-[10px] text-slate-500">
                      {po.lineItems.reduce((acc, l) => acc + l.orderedQty, 0)} units total
                    </span>
                  </td>

                  <td className="py-3.5">
                    <span className="text-white font-bold">{formatINR(po.totalAmountINR)}</span>
                  </td>

                  <td className="py-3.5">
                    {po.trackingNumber ? (
                      <div className="flex flex-col text-[10px]">
                        <span className="text-[#D4AF37] font-bold">{po.trackingNumber}</span>
                        <span className="text-slate-500">{po.inboundCarrier}</span>
                      </div>
                    ) : (
                      <span className="text-slate-500 text-[10px]">Pending ASN</span>
                    )}
                  </td>

                  <td className="py-3.5 text-right pr-2">
                    <AurixBadge
                      variant={isReceived ? 'success' : isInTransit ? 'info' : po.status === 'ACKNOWLEDGED' ? 'gold' : 'neutral'}
                      pulse={isInTransit}
                    >
                      {po.status.replace('_', ' ')}
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