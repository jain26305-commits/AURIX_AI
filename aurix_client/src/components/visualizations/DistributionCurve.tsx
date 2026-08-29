'use client';

import React from 'react';
import { AurixCard } from '@/components/ui/AurixCard';
import { AurixBadge } from '@/components/ui/AurixBadge';

export interface DistributionMetric {
  p10: number;
  p50: number;
  p90: number;
  p99?: number;
  expectedValue: number;
  unit?: string;
}

export interface DistributionCurveProps {
  title: string;
  subtitle?: string;
  metric: DistributionMetric;
  iterations?: number;
}

export const DistributionCurve: React.FC<DistributionCurveProps> = ({
  title,
  subtitle = 'Stochastic Monte Carlo Kernel Density Estimation',
  metric,
  iterations = 10000,
}) => {
  return (
    <AurixCard
      title={title}
      subtitle={subtitle}
      badge={<AurixBadge variant="gold">{iterations.toLocaleString()} ITERATIONS</AurixBadge>}
      className="space-y-6"
    >
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2">
        <div className="p-3 rounded-lg bg-white/[0.02] border border-white/[0.04]">
          <span className="text-[9px] font-mono text-slate-500 uppercase block">P10 (BEST CASE)</span>
          <span className="text-sm font-mono font-bold text-[#3DDB91]">{metric.unit}{metric.p10.toLocaleString()}</span>
        </div>
        <div className="p-3 rounded-lg bg-[#D4AF37]/10 border border-[#D4AF37]/30">
          <span className="text-[9px] font-mono text-[#D4AF37] uppercase font-bold block">P50 (MEDIAN EXPECTED)</span>
          <span className="text-base font-mono font-extrabold text-white">{metric.unit}{metric.p50.toLocaleString()}</span>
        </div>
        <div className="p-3 rounded-lg bg-white/[0.02] border border-white/[0.04]">
          <span className="text-[9px] font-mono text-slate-500 uppercase block">P90 (DOWN-SIDE RISK)</span>
          <span className="text-sm font-mono font-bold text-[#F3B33D]">{metric.unit}{metric.p90.toLocaleString()}</span>
        </div>
        <div className="p-3 rounded-lg bg-white/[0.02] border border-white/[0.04]">
          <span className="text-[9px] font-mono text-slate-500 uppercase block">EXPECTED VALUE (EV)</span>
          <span className="text-sm font-mono font-bold text-white">{metric.unit}{metric.expectedValue.toLocaleString()}</span>
        </div>
      </div>

      <div className="h-28 w-full bg-[#030303] border border-white/[0.06] rounded-lg relative overflow-hidden flex items-end p-3">
        <svg viewBox="0 0 500 100" className="w-full h-full preserve-3d overflow-visible">
          <path
            d="M 10 90 Q 150 85, 200 40 T 250 15 T 300 40 T 490 90"
            fill="none"
            stroke="#D4AF37"
            strokeWidth="2.5"
          />
          <path
            d="M 10 90 Q 150 85, 200 40 T 250 15 T 300 40 T 490 90 L 490 95 L 10 95 Z"
            fill="url(#goldGradient)"
            opacity="0.25"
          />
          <line x1="250" y1="15" x2="250" y2="90" stroke="#F0D878" strokeWidth="1.5" strokeDasharray="3 3" />
          <line x1="380" y1="65" x2="380" y2="90" stroke="#FF6B6B" strokeWidth="1.5" strokeDasharray="3 3" />
          <defs>
            <linearGradient id="goldGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#D4AF37" />
              <stop offset="100%" stopColor="#030303" stopOpacity="0" />
            </linearGradient>
          </defs>
        </svg>
      </div>
    </AurixCard>
  );
};
