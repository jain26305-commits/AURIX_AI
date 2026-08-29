'use client';

import React from 'react';
import { AurixBadge } from '@/components/ui/AurixBadge';


interface QualityScoreGaugeProps {
  score: number;
  health: 'OPTIMAL' | 'ACCEPTABLE' | 'DEGRADED';
  totalRows: number;
  totalCols: number;
  temporalStart: string;
  temporalEnd: string;
}

export const QualityScoreGauge: React.FC<QualityScoreGaugeProps> = ({
  score,
  health,
  totalRows,
  totalCols,
  temporalStart,
  temporalEnd,
}) => {
  return (
    <div className="w-full aurix-card-glass rounded-xl p-6 border border-white/[0.08] relative overflow-hidden flex flex-col md:flex-row items-center justify-between gap-6">
      {/* Specular Top Line */}
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-[#D4AF37]/40 to-transparent pointer-events-none" />

      {/* Left Metric Visual */}
      <div className="flex items-center gap-6">
        <div className="relative flex items-center justify-center">
          <div className="w-24 h-24 rounded-full border-4 border-white/10 flex flex-col items-center justify-center bg-[#07090D] shadow-[0_0_30px_rgba(212,175,55,0.15)] relative">
            <span className="text-3xl font-bold font-mono text-white tracking-tight">{score}%</span>
            <span className="text-[9px] font-mono text-gold uppercase tracking-widest mt-0.5">DQ SCORE</span>
          </div>
          {/* Circular Glow Accent */}
          <div className="absolute inset-0 rounded-full bg-[#D4AF37]/10 blur-xl pointer-events-none" />
        </div>

        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-bold text-white tracking-wide">COMPOSITE DATA INTEGRITY</h2>
            <AurixBadge variant={health === 'OPTIMAL' ? 'success' : health === 'ACCEPTABLE' ? 'warning' : 'danger'} pulse>
              {health}
            </AurixBadge>
          </div>
          <p className="text-xs font-mono text-slate-400 max-w-lg leading-relaxed">
            Deterministic audit across 7 dimensions cleared this dataset for ML forecasting, inventory target modeling, and financial exposure calculations.
          </p>
        </div>
      </div>

      {/* Right Telemetry Key-Values */}
      <div className="flex items-center gap-4 text-xs font-mono border-t md:border-t-0 md:border-l border-white/[0.08] pt-4 md:pt-0 md:pl-6">
        <div className="space-y-2">
          <div className="flex items-center justify-between gap-4 text-slate-400">
            <span>AUDITED ROWS:</span>
            <span className="text-white font-bold">{totalRows.toLocaleString()}</span>
          </div>
          <div className="flex items-center justify-between gap-4 text-slate-400">
            <span>COLUMNS:</span>
            <span className="text-white font-bold">{totalCols} mapped</span>
          </div>
          <div className="flex items-center justify-between gap-4 text-slate-400">
            <span>TIMELINE:</span>
            <span className="text-gold font-medium">{temporalStart} ➔ {temporalEnd}</span>
          </div>
        </div>
      </div>
    </div>
  );
};