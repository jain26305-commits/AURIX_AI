'use client';

import React from 'react';
import { SupplierPerformanceProfile } from '@/types/supply.types';
import { AurixCard } from '@/components/ui/AurixCard';
import { AurixBadge } from '@/components/ui/AurixBadge';


interface SupplierScorecardProps {
  supplier: SupplierPerformanceProfile;
}

export const SupplierScorecard: React.FC<SupplierScorecardProps> = ({ supplier }) => {
  return (
    <AurixCard
      title="SUPPLIER RELIABILITY SCORECARD"
      badge={
        <AurixBadge variant={supplier.riskLevel === 'LOW' ? 'success' : 'warning'}>
          {supplier.riskLevel} RISK TIER
        </AurixBadge>
      }
    >
      <div className="space-y-5 text-xs font-mono">
        <div className="flex items-center justify-between pb-3 border-b border-white/[0.06]">
          <div>
            <span className="text-sm font-bold text-white tracking-wide block">{supplier.supplierName}</span>
            <span className="text-[10px] text-slate-500">{supplier.supplierId} • Category: {supplier.primaryCategory}</span>
          </div>

          <div className="text-right">
            <span className="text-[10px] text-slate-500 uppercase block">RELIABILITY INDEX</span>
            <span className="text-xl font-bold text-[#D4AF37]">{supplier.reliabilityScorePercent}%</span>
          </div>
        </div>

        {/* Key Operational KPI Grid */}
        <div className="grid grid-cols-3 gap-3 text-center">
          <div className="p-3 rounded-lg bg-white/[0.02] border border-white/[0.06]">
            <span className="text-[10px] text-slate-500 uppercase block">OTIF RATE</span>
            <span className="text-base font-bold text-[#3DDB91] mt-0.5 block">{supplier.onTimeInFullPercent}%</span>
          </div>

          <div className="p-3 rounded-lg bg-white/[0.02] border border-white/[0.06]">
            <span className="text-[10px] text-slate-500 uppercase block">FILL RATE</span>
            <span className="text-base font-bold text-white mt-0.5 block">{supplier.fillRatePercent}%</span>
          </div>

          <div className="p-3 rounded-lg bg-white/[0.02] border border-white/[0.06]">
            <span className="text-[10px] text-slate-500 uppercase block">DELAY PROBABILITY</span>
            <span className="text-base font-bold text-[#F3B33D] mt-0.5 block">
              {supplier.orderDelayProbabilityPercent}%
            </span>
          </div>
        </div>

        {/* Qualitative Dispatch Note */}
        <div className="p-3 rounded-lg bg-white/[0.02] border border-white/[0.04] text-[11px] leading-relaxed text-slate-300">
          <span className="text-gold font-bold block mb-1">VENDOR PROVENANCE NOTE:</span>
          {supplier.recommendationNotes}
        </div>
      </div>
    </AurixCard>
  );
};