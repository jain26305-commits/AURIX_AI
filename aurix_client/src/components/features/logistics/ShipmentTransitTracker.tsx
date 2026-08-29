'use client';

import React from 'react';
import { ActiveShipment } from '@/types/logistics.types';
import { Truck } from 'lucide-react';
import { AurixBadge } from '@/components/ui/AurixBadge';

interface ShipmentTransitTrackerProps {
  shipments: ActiveShipment[];
}

export const ShipmentTransitTracker: React.FC<ShipmentTransitTrackerProps> = ({ shipments }) => {
  return (
    <div className="w-full aurix-card-glass rounded-xl p-6 border border-white/[0.08]">
      <div className="flex items-center justify-between pb-4 mb-4 border-b border-white/[0.06]">
        <div>
          <h3 className="text-sm font-semibold text-white tracking-wide flex items-center gap-2">
            <Truck className="w-4 h-4 text-gold" />
            ACTIVE SHIPMENT MANIFESTS & DELAY VARIANCES
          </h3>
          <p className="text-[11px] font-mono text-slate-400 mt-0.5">
            Real-time delivery milestones, cargo valuations, and projected ETA breaches.
          </p>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs font-mono">
          <thead>
            <tr className="border-b border-white/[0.08] text-slate-500 text-[10px] uppercase tracking-wider">
              <th className="pb-3 pl-2">Tracking / PO</th>
              <th className="pb-3">Route Corridor</th>
              <th className="pb-3">Mode & Carrier</th>
              <th className="pb-3">Manifest Value</th>
              <th className="pb-3">Estimated Arrival</th>
              <th className="pb-3">Delay Risk</th>
              <th className="pb-3 text-right pr-2">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/[0.04]">
            {shipments.map((s) => {
              const isDelayed = s.status === 'DELAYED' || s.status === 'CUSTOMS_HOLD';

              return (
                <tr key={s.trackingId} className={`hover:bg-white/[0.02] transition-colors ${isDelayed ? 'bg-[#FF6B6B]/[0.025]' : ''}`}>
                  <td className="py-3 pl-2">
                    <div className="flex flex-col">
                      <span className="text-white font-bold">{s.trackingId}</span>
                      <span className="text-[10px] text-gold">{s.poNumber}</span>
                    </div>
                  </td>

                  <td className="py-3">
                    <span className="text-slate-300 block">{s.originHub}</span>
                    <span className="text-[10px] text-slate-500 block">➔ {s.destinationHub}</span>
                  </td>

                  <td className="py-3">
                    <span className="text-slate-300 block">{s.transportMode}</span>
                    <span className="text-[10px] text-slate-500 block">{s.carrierName}</span>
                  </td>

                  <td className="py-3">
                    <span className="text-white font-bold block">₹{(s.shipmentValueINR / 100000).toFixed(2)}L</span>
                    <span className="text-[10px] text-slate-500 block">{s.totalUnits} units</span>
                  </td>

                  <td className="py-3">
                    <span className="text-slate-300 block">{s.estimatedArrival}</span>
                    {s.delayVarianceDays > 0 && (
                      <span className="text-[#FF8585] text-[10px] block font-bold">
                        +{s.delayVarianceDays}d variance
                      </span>
                    )}
                  </td>

                  <td className="py-3">
                    <span className={s.delayProbabilityPercent > 50 ? 'text-[#FF6B6B] font-bold' : 'text-[#3DDB91]'}>
                      {s.delayProbabilityPercent}%
                    </span>
                  </td>

                  <td className="py-3 text-right pr-2">
                    {s.status === 'DELAYED' && <AurixBadge variant="danger" pulse>DELAYED</AurixBadge>}
                    {s.status === 'CUSTOMS_HOLD' && <AurixBadge variant="warning" pulse>CUSTOMS HOLD</AurixBadge>}
                    {s.status === 'IN_TRANSIT' && <AurixBadge variant="info">IN TRANSIT</AurixBadge>}
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