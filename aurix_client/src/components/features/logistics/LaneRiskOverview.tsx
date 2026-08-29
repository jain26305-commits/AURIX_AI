'use client';

import React from 'react';
import { TransitLaneMetrics } from '@/types/logistics.types';

import { AurixBadge } from '@/components/ui/AurixBadge';
import { Compass } from 'lucide-react';

interface LaneRiskOverviewProps {
  lanes: TransitLaneMetrics[];
}

export const LaneRiskOverview: React.FC<LaneRiskOverviewProps> = ({ lanes }) => {
  return (
    <div className="w-full aurix-card-glass rounded-xl p-6 border border-white/[0.08]">
      <div className="flex items-center justify-between pb-4 mb-4 border-b border-white/[0.06]">
        <div>
          <h3 className="text-sm font-semibold text-white tracking-wide flex items-center gap-2">
            <Compass className="w-4 h-4 text-[#D4AF37]" />
            FREIGHT CORRIDOR & TRANSIT LANE RISK PROFILES
          </h3>
          <p className="text-[11px] font-mono text-slate-400 mt-0.5">
            Turnaround quantiles, bottleneck probability, and active inventory in transit.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs font-mono">
        {lanes.map((lane) => {
          const isCritical = lane.riskLevel === 'CRITICAL';
          const isModerate = lane.riskLevel === 'MODERATE';

          return (
            <div
              key={lane.laneId}
              className={`p-5 rounded-xl border flex flex-col justify-between transition-all duration-200 ${
                isCritical
                  ? 'bg-[#FF6B6B]/5 border-[#FF6B6B]/30'
                  : isModerate
                  ? 'bg-[#F3B33D]/5 border-[#F3B33D]/25'
                  : 'bg-white/[0.02] border-white/[0.06]'
              }`}
            >
              <div>
                <div className="flex items-center justify-between">
                  <span className="text-[10px] text-slate-500 font-bold">{lane.laneId}</span>
                  <AurixBadge variant={isCritical ? 'danger' : isModerate ? 'warning' : 'success'}>
                    {lane.riskLevel}
                  </AurixBadge>
                </div>

                <div className="mt-3 space-y-0.5">
                  <span className="text-white font-bold text-xs block">{lane.origin}</span>
                  <span className="text-slate-500 text-[10px] block">➔ {lane.destination}</span>
                </div>

                <div className="grid grid-cols-2 gap-2 mt-4 pt-3 border-t border-white/[0.04] text-[11px]">
                  <div>
                    <span className="text-slate-500 block text-[9px]">AVG / P90 LEAD</span>
                    <span className="text-white font-bold">{lane.avgTransitDays}d / {lane.p90TransitDays}d</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block text-[9px]">ON-TIME RATE</span>
                    <span className={lane.onTimeReliabilityPercent >= 90 ? 'text-[#3DDB91] font-bold' : 'text-[#F3B33D] font-bold'}>
                      {lane.onTimeReliabilityPercent}%
                    </span>
                  </div>
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-white/[0.04] flex items-center justify-between text-[10px] text-slate-400">
                <span>IN TRANSIT: {lane.totalUnitsInTransit} pcs</span>
                <span className="text-gold font-bold">₹{(lane.totalCapitalInTransitINR / 100000).toFixed(1)}L</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};