'use client';

import React from 'react';
import { AdvanceShippingNotice } from '@/types/procurement.types';
import { AurixBadge } from '@/components/ui/AurixBadge';

interface AsnTrackerProps {
  asns: AdvanceShippingNotice[];
}

export const AsnTracker: React.FC<AsnTrackerProps> = ({ asns }) => {
  return (
    <div className="w-full aurix-card-glass rounded-xl p-6 border border-white/[0.08] select-none font-mono">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="border-b border-white/[0.08] text-slate-500 text-[10px] uppercase tracking-wider">
              <th className="pb-3 pl-2">ASN & Reference PO</th>
              <th className="pb-3">Vendor Dispatch</th>
              <th className="pb-3">Carrier & Manifest Tracking</th>
              <th className="pb-3">Shipped Date</th>
              <th className="pb-3">Arrival Schedule</th>
              <th className="pb-3">Volume Cargo</th>
              <th className="pb-3 text-right pr-2">Transit State</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/[0.04]">
            {asns.map((asn) => (
              <tr key={asn.asnNumber} className="hover:bg-white/[0.02] transition-colors">
                <td className="py-3.5 pl-2">
                  <span className="text-white font-bold text-xs block">{asn.asnNumber}</span>
                  <span className="text-gold text-[10px]">{asn.poNumber}</span>
                </td>

                <td className="py-3.5 text-slate-300 font-medium">{asn.vendorName}</td>

                <td className="py-3.5">
                  <span className="text-[#D4AF37] font-bold block">{asn.trackingNumber}</span>
                  <span className="text-slate-500 text-[10px]">{asn.carrier}</span>
                </td>

                <td className="py-3.5 text-slate-400">{asn.shippedDate}</td>
                <td className="py-3.5 text-white font-bold">{asn.estimatedArrival}</td>

                <td className="py-3.5">
                  <span className="text-white font-bold block">{asn.totalUnits.toLocaleString()} units</span>
                  <span className="text-slate-500 text-[10px]">{asn.itemCount} SKUs</span>
                </td>

                <td className="py-3.5 text-right pr-2">
                  <AurixBadge
                    variant={asn.status === 'DELIVERED' ? 'success' : asn.status === 'IN_TRANSIT' ? 'info' : 'gold'}
                    pulse={asn.status === 'IN_TRANSIT'}
                  >
                    {asn.status.replace('_', ' ')}
                  </AurixBadge>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};