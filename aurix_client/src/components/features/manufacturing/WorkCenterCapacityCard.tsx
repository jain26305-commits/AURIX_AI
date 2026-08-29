'use client';

import React from 'react';

import { AurixBadge } from '@/components/ui/AurixBadge';
import { Factory } from 'lucide-react';

interface WorkCenterCapacityCardProps {
  workCenters?: any[];
}

export const WorkCenterCapacityCard: React.FC<WorkCenterCapacityCardProps> = ({ workCenters }) => {
  return (
    <div className="w-full aurix-card-glass rounded-xl p-6 border border-white/[0.08] select-none font-mono space-y-6">
      <div className="flex items-center justify-between pb-4 mb-2 border-b border-white/[0.06]">
        <div>
          <h3 className="text-sm font-bold text-white tracking-wide flex items-center gap-2">
            <Factory className="w-4 h-4 text-gold" />
            WORK CENTER CAPACITY & MACHINE CONSTRAINTS
          </h3>
          <p className="text-[11px] text-slate-400 mt-0.5">
            Load vs. weekly rated capacity hours across fabrication, dyeing, cutting, and stitching bays.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {(workCenters || []).map((wc) => {
          const isCritical = wc.status === 'CRITICAL';
          const isOptimal = wc.status === 'OPTIMAL';

          return (
            <div
              key={wc.workCenterId}
              className={`p-4 rounded-xl border space-y-3 ${
                isCritical
                  ? 'bg-[#FF6B6B]/[0.03] border-[#FF6B6B]/40 shadow-[0_0_20px_rgba(255,107,107,0.1)]'
                  : 'bg-white/[0.02] border-white/[0.06]'
              }`}
            >
              <div className="flex items-start justify-between gap-2">
                <div>
                  <span className="text-white font-bold text-xs block">{wc.workCenterName}</span>
                  <span className="text-slate-500 text-[10px] mt-0.5 block">{wc.facilityLocation} • {wc.workCenterId}</span>
                </div>
                <AurixBadge variant={isCritical ? 'danger' : isOptimal ? 'success' : 'warning'} pulse={isCritical}>
                  {((wc.utilizationPercent || 0) || 0)}% LOAD
                </AurixBadge>
              </div>

              {/* Capacity Progress Meter */}
              <div className="space-y-1.5">
                <div className="flex justify-between text-[10px] text-slate-400">
                  <span>Allocated: {wc.allocatedLoadHours}h</span>
                  <span>Rated Cap: {wc.weeklyCapacityHours}h/wk</span>
                </div>
                <div className="w-full h-2 bg-white/5 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${
                      isCritical
                        ? 'bg-gradient-to-r from-gold to-[#FF6B6B]'
                        : 'bg-gradient-to-r from-[#B8912A] to-[#D4AF37]'
                    }`}
                    style={{ width: `${Math.min(100, ((wc.utilizationPercent || 0) || 0))}%` }}
                  />
                </div>
              </div>

              <div className="p-2.5 rounded-lg bg-white/[0.02] border border-white/[0.04] text-[10px] text-slate-400">
                <span className="text-gold font-bold block mb-0.5">CONSTRAINING OPERATION:</span>
                {wc.primaryConstrainingOperation}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};