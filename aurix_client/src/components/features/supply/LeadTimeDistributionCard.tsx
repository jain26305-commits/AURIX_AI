'use client';

import React from 'react';
import { LeadTimeDistribution } from '@/types/supply.types';
import { AurixCard } from '@/components/ui/AurixCard';


interface LeadTimeDistributionCardProps {
  leadTime: LeadTimeDistribution;
  supplierName: string;
}

export const LeadTimeDistributionCard: React.FC<LeadTimeDistributionCardProps> = ({
  leadTime,
  supplierName,
}) => {
  return (
    <AurixCard
      title="EMPIRICAL LEAD-TIME QUANTILES"
      subtitle={`Turnaround distribution derived from ${leadTime.sampleDeliveriesCount} verified PO receipts for ${supplierName}`}
    >
      <div className="space-y-6 text-xs font-mono">
        {/* Quantile Highlights */}
        <div className="grid grid-cols-5 gap-2 text-center">
          <div className="p-2.5 rounded-lg bg-white/[0.02] border border-white/[0.06]">
            <span className="text-[9px] text-slate-500 block uppercase">MEAN (AVG)</span>
            <span className="text-sm font-bold text-white">{leadTime.meanDays}d</span>
          </div>
          <div className="p-2.5 rounded-lg bg-white/[0.02] border border-white/[0.06]">
            <span className="text-[9px] text-slate-500 block uppercase">MEDIAN (P50)</span>
            <span className="text-sm font-bold text-[#D4AF37]">{leadTime.medianDays}d</span>
          </div>
          <div className="p-2.5 rounded-lg bg-white/[0.02] border border-white/[0.06]">
            <span className="text-[9px] text-slate-500 block uppercase">P75</span>
            <span className="text-sm font-bold text-white">{leadTime.p75Days}d</span>
          </div>
          <div className="p-2.5 rounded-lg bg-gold/10 border border-gold/30">
            <span className="text-[9px] text-gold block uppercase font-bold">P90 TARGET</span>
            <span className="text-sm font-bold text-gold">{leadTime.p90Days}d</span>
          </div>
          <div className="p-2.5 rounded-lg bg-[#FF6B6B]/10 border border-[#FF6B6B]/30">
            <span className="text-[9px] text-[#FF8585] block uppercase font-bold">P95 (TAIL)</span>
            <span className="text-sm font-bold text-[#FF8585]">{leadTime.p95Days}d</span>
          </div>
        </div>

        {/* Histogram Bins */}
        <div className="space-y-2">
          <span className="text-[10px] text-slate-500 uppercase tracking-widest font-bold block">
            HISTORICAL FREQUENCY DISTRIBUTION
          </span>
          <div className="space-y-2">
            {leadTime.frequencyBins.map((bin) => (
              <div key={bin.daysRange} className="flex items-center gap-3">
                <span className="w-16 text-[10px] text-slate-400 shrink-0">{bin.daysRange}</span>
                <div className="flex-1 h-3 bg-white/5 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-[#B8912A] to-[#D4AF37] rounded-full"
                    style={{ width: `${bin.frequencyPercent}%` }}
                  />
                </div>
                <span className="w-10 text-[10px] text-white font-bold text-right">{bin.frequencyPercent}%</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </AurixCard>
  );
};